import { useMemo } from 'react';
import { jwtDecode } from "jwt-decode";

/**
 * Hook to manage and check user permissions.
 * Permissions are extracted from the JWT token and stored in localStorage.
 */
export const usePermissions = () => {
  const token = localStorage.getItem("token");

  const authData = useMemo(() => {
    if (!token) return { role: 'guest', permissions: [], user: null };
    try {
      const decodedUser = jwtDecode(token);
      const normalizedRole = decodedUser?.role ? decodedUser.role.toLowerCase() : 'guest';
      
      let permissions = decodedUser?.permissions || [];
      if (typeof permissions === 'string') {
        try {
          permissions = JSON.parse(permissions);
        } catch (e) {
          permissions = [];
        }
      }

      return {
        role: normalizedRole,
        permissions: Array.isArray(permissions) ? permissions : [],
        user: decodedUser,
      };
    } catch (error) {
      console.error("Invalid token", error);
      return { role: 'guest', permissions: [], user: null };
    }
  }, [token]);

  const { role, permissions, user } = authData;
  const isSuperadmin = role === 'admin' || user?.is_superadmin;

  const hasPermission = (permission) => {
    if (isSuperadmin) return true;
    if (!permission) return true;
    
    const permsToCheck = Array.isArray(permission) ? permission : [permission];
    
    return permsToCheck.some(targetPerm => {
      const permToCheck = targetPerm.toLowerCase();
      
      return permissions.some(p => {
        if (typeof p !== 'string') return false;
        const userPerm = p.toLowerCase();
        
        // Exact match
        if (userPerm === permToCheck) return true;
        
        // singular/plural mismatch handling
        const singular = permToCheck.replace(/s:view$/, ':view').replace(/s:create$/, ':create').replace(/s:edit$/, ':edit').replace(/s:delete$/, ':delete');
        const plural = permToCheck.includes(':') 
          ? permToCheck.replace(/:/, 's:') 
          : permToCheck + 's';
          
        if (userPerm === singular || userPerm === plural) return true;

        // Module:action match
        if (permToCheck.includes(':')) {
          const [module, action] = permToCheck.split(':');
          // Handle module:* or module:view patterns
          if (userPerm === `${module}:*` || userPerm === `${module}:view`) {
            if (action === 'view' || action === 'read') return true;
          }
        }
        
        return false;
      });
    }) || permissions.includes('*');
  };

  const hasAnyPermission = (requiredPermissions) => {
    return hasPermission(requiredPermissions);
  };

  const hasModuleAccess = (moduleId) => {
    if (isSuperadmin) return true;
    const ids = Array.isArray(moduleId) ? moduleId : [moduleId];
    
    return permissions.some(p => {
      if (typeof p !== 'string') return false;
      const userPerm = p.toLowerCase();
      return ids.some(id => {
        const nid = id.toLowerCase();
        return userPerm.startsWith(`${nid}:`) || 
               userPerm.startsWith(`${nid}_`) || 
               userPerm === nid ||
               userPerm.startsWith(`${nid}s:`) || // handle plural module
               userPerm.startsWith(`${nid}s_`);
      });
    });
  };

  return { permissions, hasPermission, hasAnyPermission, hasModuleAccess, role, user, isSuperadmin, isAdmin: isSuperadmin };
};

