from app.curd import guest as crud_guest # Import the CRUD functions we defined
from app.models.guest import Guest as GuestModel # Import the SQLAlchemy model
from app.schemas.guest import GuestCreate, GuestOut, GuestUpdate

@router.post("/", response_model=GuestOut, status_code=status.HTTP_201_CREATED)
def create_guest(guest: GuestCreate, db: Session = Depends(get_db)):
    """
    Creates a new guest account.
    """
    try:
        db_guest = crud_guest.create_guest(db=db, guest=guest)
        return db_guest
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[GuestOut])
def read_guests(db: Session = Depends(get_db)):
    """
    Retrieves a list of all guests.
    """
    guests = crud_guest.get_guests(db)
    return guests

@router.get("/{guest_id}", response_model=GuestOut)
def read_guest(guest_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a single guest by their ID.
    """
    db_guest = crud_guest.get_guest_by_id(db, guest_id=guest_id)
    if not db_guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return db_guest

@router.put("/{guest_id}", response_model=GuestOut)
def update_guest(guest_id: int, guest: GuestUpdate, db: Session = Depends(get_db)):
    """
    Updates an existing guest's profile.
    """
    db_guest = crud_guest.update_guest(db, guest_id=guest_id, guest=guest)
    if not db_guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    return db_guest

@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(guest_id: int, db: Session = Depends(get_db)):
    """
    Deletes a guest account by ID.
    """
    db_guest = crud_guest.get_guest_by_id(db, guest_id=guest_id)
    if not db_guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    crud_guest.delete_guest(db, guest_id=guest_id)

