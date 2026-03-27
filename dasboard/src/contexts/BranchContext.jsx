import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const BranchContext = createContext();

export const useBranch = () => {
    const context = useContext(BranchContext);
    if (!context) {
        throw new Error('useBranch must be used within a BranchProvider');
    }
    return context;
};

export const BranchProvider = ({ children }) => {
    const [branches, setBranches] = useState([]);
    const [activeBranchId, setActiveBranchId] = useState(
        localStorage.getItem('activeBranchId') || 'all'
    );
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchBranches();
    }, []);

    const fetchBranches = async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            const response = await api.get('/branches');
            setBranches(response.data);

            // If activeBranchId is 'all', we keep it. Otherwise, check if valid.
            if (activeBranchId !== 'all' && response.data.length > 0) {
                const isValid = response.data.some(b => b.id.toString() === activeBranchId.toString());
                if (!isValid) {
                    switchBranch('all');
                }
            }
        } catch (error) {
            console.error('Error fetching branches:', error);
        } finally {
            setLoading(false);
        }
    };

    const switchBranch = (branchId) => {
        setActiveBranchId(branchId);
        localStorage.setItem('activeBranchId', branchId);
        // Force a page reload or trigger a global data refresh
        window.location.reload();
    };

    const activeBranch = branches.find(b => b.id.toString() === activeBranchId.toString());

    return (
        <BranchContext.Provider value={{
            branches,
            activeBranchId,
            activeBranch,
            switchBranch,
            loading,
            refreshBranches: fetchBranches
        }}>
            {children}
        </BranchContext.Provider>
    );
};
