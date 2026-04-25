import pytest
from datetime import date, timedelta, datetime
import json
from app.models.employee import Employee, Leave, Attendance, WorkingLog
from app.models.branch import Branch
from app.models.user import User, Role
from app.models.salary_payment import SalaryPayment
from app.models.settings import SystemSetting
from app.utils.auth import get_password_hash, create_access_token

class TestEmployeeScopingAudit:
    """
    Comprehensive audit tests for Employee Management multi-tenancy.
    Verifies isolation across Directory, Leaves, Attendance, and Payroll.
    """

    def setup_branch_data(self, db_session, name, code):
        """Seeds a branch with employees and related data."""
        branch = Branch(name=name, code=code, is_active=True)
        db_session.add(branch)
        db_session.flush()

        role = db_session.query(Role).filter(Role.name == "admin").first()
        if not role:
            role = Role(name="admin", permissions="all")
            db_session.add(role)
            db_session.flush()

        user = User(
            name=f"Manager {code}", 
            email=f"mgr.{code}@test.com", 
            hashed_password=get_password_hash("pass"),
            branch_id=branch.id,
            role_id=role.id,
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Create 2 employees
        emp1 = Employee(
            name=f"Staff {code} 1", role="Reception", salary=25000, 
            join_date=date.today(), branch_id=branch.id,
            daily_tasks=json.dumps(["Check-in List", "Phone Logs"])
        )
        emp2 = Employee(
            name=f"Staff {code} 2", role="Housekeeping", salary=18000, 
            join_date=date.today(), branch_id=branch.id
        )
        db_session.add_all([emp1, emp2])
        db_session.flush()

        db_session.commit()
        return branch, user, [emp1, emp2]

    def test_directory_isolation(self, authorized_client, db_session):
        """Verify that employee directory is strictly scoped by branch."""
        branch_a, user_a, emps_a = self.setup_branch_data(db_session, "Alpha", "A")
        branch_b, user_b, emps_b = self.setup_branch_data(db_session, "Beta", "B")

        # 1. Branch A Admin - Should see only Branch A staff
        headers_a = {"X-Branch-ID": str(branch_a.id)}
        resp = authorized_client.get("/api/employees", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        names = [e["name"] for e in data]
        assert "Staff A 1" in names
        assert "Staff B 1" not in names

        # 2. Enterprise View - Should see all staff
        headers_all = {"X-Branch-ID": "all"}
        resp = authorized_client.get("/api/employees", headers=headers_all)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 4
        names = [e["name"] for e in data]
        assert "Staff A 1" in names
        assert "Staff B 1" in names

    def test_leave_workflow_scoping(self, authorized_client, db_session):
        """Verify leave applications and pending list are correctly scoped."""
        branch_a, user_a, emps_a = self.setup_branch_data(db_session, "Alpha", "A")
        branch_b, user_b, emps_b = self.setup_branch_data(db_session, "Beta", "B")

        # 1. Apply Leave in Branch A
        headers_a = {"X-Branch-ID": str(branch_a.id)}
        leave_data = {
            "employee_id": emps_a[0].id,
            "from_date": str(date.today() + timedelta(days=5)),
            "to_date": str(date.today() + timedelta(days=7)),
            "reason": "Family function",
            "leave_type": "Paid"
        }
        resp = authorized_client.post("/api/employees/leave", json=leave_data, headers=headers_a)
        assert resp.status_code == 200
        leave_id = resp.json()["id"]

        # 2. Verify Pending Leaves in Branch A - Should show 1
        resp = authorized_client.get("/api/employees/pending-leaves", headers=headers_a)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 3. Verify Pending Leaves in Branch B - Should show 0 (Isolated)
        headers_b = {"X-Branch-ID": str(branch_b.id)}
        resp = authorized_client.get("/api/employees/pending-leaves", headers=headers_b)
        assert resp.status_code == 200
        assert len(resp.json()) == 0

        # 4. Enterprise View - Should show the leave
        headers_all = {"X-Branch-ID": "all"}
        resp = authorized_client.get("/api/employees/pending-leaves", headers=headers_all)
        assert resp.status_code == 200
        ids = [l["id"] for l in resp.json()]
        assert leave_id in ids

    def test_attendance_and_task_workflow(self, authorized_client, db_session):
        """Verify Clock-in/out workflow with task completion requirement."""
        branch_a, _, emps_a = self.setup_branch_data(db_session, "Alpha", "A")
        emp = emps_a[0] # Has 2 tasks assigned: Check-in List, Phone Logs
        headers_a = {"X-Branch-ID": str(branch_a.id)}

        # 1. Clock-in
        clock_in_data = {"employee_id": emp.id, "location": "Reception Desk"}
        resp = authorized_client.post("/api/attendance/clock-in", json=clock_in_data, headers=headers_a)
        assert resp.status_code == 200
        log_id = resp.json()["id"]

        # 2. Attempt Clock-out without tasks - Should FAIL (400)
        clock_out_data = {"employee_id": emp.id}
        resp = authorized_client.post("/api/attendance/clock-out", json=clock_out_data, headers=headers_a)
        assert resp.status_code == 400
        assert "complete all assigned active shift tasks" in resp.json()["detail"]

        # 3. Complete some tasks
        tasks_data = {"completed_tasks": json.dumps(["Check-in List"])}
        resp = authorized_client.put(f"/api/attendance/work-logs/{log_id}/tasks", json=tasks_data, headers=headers_a)
        assert resp.status_code == 200

        # 4. Attempt Clock-out (still missing one task) - Should FAIL
        resp = authorized_client.post("/api/attendance/clock-out", json=clock_out_data, headers=headers_a)
        assert resp.status_code == 400

        # 5. Complete all tasks
        tasks_data = {"completed_tasks": json.dumps(["Check-in List", "Phone Logs"])}
        resp = authorized_client.put(f"/api/attendance/work-logs/{log_id}/tasks", json=tasks_data, headers=headers_a)
        assert resp.status_code == 200

        # 6. Success Clock-out
        resp = authorized_client.post("/api/attendance/clock-out", json=clock_out_data, headers=headers_a)
        assert resp.status_code == 200
        assert resp.json()["check_out_time"] is not None

    def test_payroll_scoping(self, authorized_client, db_session):
        """Verify that salary payments are isolated by branch."""
        branch_a, _, emps_a = self.setup_branch_data(db_session, "Alpha", "A")
        branch_b, _, emps_b = self.setup_branch_data(db_session, "Beta", "B")

        # 1. Create Payment in Branch A
        headers_a = {"X-Branch-ID": str(branch_a.id)}
        payment_data = {
            "month": "April", "year": 2026, "month_number": 4,
            "basic_salary": 25000.0, "allowances": 1000.0, "deductions": 500.0,
            "payment_method": "upi", "notes": "On-time"
        }
        resp = authorized_client.post(f"/api/employees/{emps_a[0].id}/salary-payments", json=payment_data, headers=headers_a)
        assert resp.status_code == 200

        # 2. Fetch History in Branch A - Should find 1
        resp = authorized_client.get(f"/api/employees/{emps_a[0].id}/salary-payments", headers=headers_a)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # 3. Fetch History in Branch B - Should find 0 (Isolated)
        headers_b = {"X-Branch-ID": str(branch_b.id)}
        resp = authorized_client.get(f"/api/employees/{emps_a[0].id}/salary-payments", headers=headers_b)
        assert resp.status_code == 200
        assert len(resp.json()) == 0

    def test_config_policy_isolation(self, authorized_client, db_session):
        """Verify leave policy updates (global settings but verifies logic)."""
        # Policies are currently global in SystemSetting, but we verify they are accessible
        resp = authorized_client.get("/api/employees/leave-policy")
        assert resp.status_code == 200
        
        new_policy = {"paid_leave_yearly": 20, "sick_leave_yearly": 10}
        resp = authorized_client.post("/api/employees/leave-policy", json=new_policy)
        assert resp.status_code == 200
        
        resp = authorized_client.get("/api/employees/leave-policy")
        assert resp.json()["paid_leave_yearly"] == 20
