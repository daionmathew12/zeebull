import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layout/DashboardLayout';
import api from '../services/api';
import { User, Mail, Phone, Bed, Utensils, ConciergeBell, FileText, Camera, Search, AlertCircle } from 'lucide-react';
import { getImageUrl } from '../utils/imageUtils';

const InfoCard = ({ icon, label, value }) => (
    <div className="flex items-center text-gray-700">
        {icon}
        <span className="font-semibold ml-2 mr-1">{label}:</span>
        <span>{value}</span>
    </div>
);

const SectionCard = ({ title, children }) => (
    <div className="bg-white p-6 rounded-xl shadow-md">
        <h3 className="text-xl font-bold text-gray-800 mb-4">{title}</h3>
        <div className="overflow-x-auto">
            {children}
        </div>
    </div>
);

const ensureProofPath = (url) => {
    if (!url) return url;
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    if (url.includes('/')) return url; // Path already included
    return `uploads/checkin_proofs/${url}`;
};


const GuestProfile = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [mobile, setMobile] = useState('');
    const [bookingId, setBookingId] = useState('');
    const [roomNumber, setRoomNumber] = useState('');
    const [stayDate, setStayDate] = useState('');
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [suggestions, setSuggestions] = useState([]);

    useEffect(() => {
        const fetchSuggestions = async () => {
            try {
                const response = await api.get('/reports/guest-suggestions');
                setSuggestions(response.data);
            } catch (err) {
                console.error("Could not fetch guest suggestions:", err);
            }
        };
        fetchSuggestions();
    }, []);

    const triggerSearch = async (searchParams) => {
        if (!searchParams.email && !searchParams.mobile && !searchParams.name && !searchParams.bookingId && !searchParams.roomNumber) {
            setError('Please provide at least one search criteria.');
            return;
        }
        setLoading(true);
        setError('');
        setProfile(null);

        try {
            const response = await api.get('/reports/guest-profile', {
                params: {
                    ...(searchParams.name && { guest_name: searchParams.name }),
                    ...(searchParams.email && { guest_email: searchParams.email }),
                    ...(searchParams.mobile && { guest_mobile: searchParams.mobile }),
                    ...(searchParams.bookingId && { booking_id: searchParams.bookingId }),
                    ...(searchParams.roomNumber && { room_number: searchParams.roomNumber }),
                    ...(searchParams.stayDate && { stay_date: searchParams.stayDate }),
                }
            });
            setProfile(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to fetch guest profile.');
        } finally {
            setLoading(false);
        }
    }

    const handleSearch = async (e) => {
        e.preventDefault();
        triggerSearch({ name, email, mobile, bookingId, roomNumber, stayDate });
    };

    const handleSuggestionClick = (suggestion) => {
        // Populate the form fields
        setName(suggestion.guest_name || '');
        setEmail(suggestion.guest_email || '');
        setMobile(suggestion.guest_mobile || '');
        setBookingId('');
        setRoomNumber('');
        setStayDate('');
        
        // Immediately trigger the search
        triggerSearch({
            name: suggestion.guest_name,
            email: suggestion.guest_email,
            mobile: suggestion.guest_mobile
        });
    };

    return (
        <DashboardLayout>
            {/* Animated Background */}
            <div className="bubbles-container">
                <li></li>
                <li></li>
                <li></li>
                <li></li>
                <li></li>
                <li></li>
                <li></li>
                <li></li>
                <li></li>
                <li></li>
            </div>

            <div className="p-6 bg-gray-50 min-h-screen">
                <h1 className="text-3xl font-bold text-gray-800 mb-6">Guest Profile Report</h1>

                {/* Guest Suggestions Horizontal List */}
                <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-700 mb-3">Quick Search</h3>
                    <div className="flex space-x-3 overflow-x-auto pb-3">
                        {suggestions.map((s, i) => (
                            <button
                                key={i}
                                onClick={() => handleSuggestionClick(s)}
                                className="flex-shrink-0 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-full text-sm font-medium hover:bg-indigo-50 hover:border-indigo-400 transition-colors shadow-sm"
                            >
                                {s.guest_name}
                            </button>
                        ))}
                        {suggestions.length === 0 && (
                            <p className="text-sm text-gray-500">No guest suggestions available.</p>
                        )}
                    </div>
                </div>

                {/* Search Form */}
                <div className="max-w-4xl mx-auto bg-white p-6 rounded-xl shadow-md mb-8">
                    <form onSubmit={handleSearch} className="flex flex-col gap-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                            <input
                                type="text"
                                placeholder="Guest Name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            <input
                                type="email"
                                placeholder="Guest Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                list="guest-emails"
                            />
                            <datalist id="guest-emails">
                                {suggestions.map((s, i) => (
                                    <option key={i} value={s.guest_email}>{s.guest_name} ({s.guest_mobile})</option>
                                ))}
                            </datalist>
                            <input
                                type="tel"
                                placeholder="Guest Mobile"
                                value={mobile}
                                onChange={(e) => setMobile(e.target.value)}
                                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            
                            <input
                                type="text"
                                placeholder="Booking ID (e.g. BK-00001)"
                                value={bookingId}
                                onChange={(e) => setBookingId(e.target.value)}
                                className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            />
                            
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Room No."
                                    value={roomNumber}
                                    onChange={(e) => setRoomNumber(e.target.value)}
                                    className="w-1/2 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                />
                                <input
                                    type="date"
                                    placeholder="Stay Date"
                                    value={stayDate}
                                    title="Stay Date (Required with Room No.)"
                                    onChange={(e) => setStayDate(e.target.value)}
                                    className="w-1/2 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                                />
                            </div>
                        </div>
                        <div className="flex justify-end">
                            <button
                                type="submit"
                                className="w-full sm:w-auto bg-indigo-600 text-white px-8 py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition flex items-center justify-center shadow-md hover:shadow-lg"
                                disabled={loading}
                            >
                                <Search size={18} className="mr-2" />
                                {loading ? 'Searching...' : 'Search Profiles'}
                            </button>
                        </div>
                    </form>
                </div>

                {error && (
                    <div className="max-w-2xl mx-auto bg-red-100 text-red-700 p-4 rounded-lg flex items-center">
                        <AlertCircle size={20} className="mr-3" />
                        {error}
                    </div>
                )}

                {profile && (
                    <div className="space-y-8 animate-fade-in">
                        {/* Guest Details */}
                        <SectionCard title="Guest Details">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <InfoCard icon={<User size={20} className="text-indigo-500" />} label="Name" value={profile.guest_details.name} />
                                <InfoCard icon={<Mail size={20} className="text-indigo-500" />} label="Email" value={profile.guest_details.email} />
                                <InfoCard icon={<Phone size={20} className="text-indigo-500" />} label="Mobile" value={profile.guest_details.mobile} />
                            </div>
                        </SectionCard>

                        {/* Booking History */}
                        <SectionCard title="Booking History">
                            <table className="min-w-full text-sm">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="p-3 text-left">Type</th>
                                        <th className="p-3 text-left">Dates</th>
                                        <th className="p-3 text-left">Rooms</th>
                                        <th className="p-3 text-left">Status</th>
                                        <th className="p-3 text-left">Documents</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {profile.bookings.map(b => (
                                        <tr key={`${b.type}-${b.id}`}>
                                            <td className="p-3">{b.type}</td>
                                            <td className="p-3">{b.check_in} to {b.check_out}</td>
                                            <td className="p-3">{b.rooms.join(', ')}</td>
                                            <td className="p-3"><span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">{b.status}</span></td>
                                            <td className="p-3 flex items-center gap-4">
                                                {b.id_card_image_url && <a href={getImageUrl(ensureProofPath(b.id_card_image_url))} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline flex items-center"><FileText size={16} className="mr-1" /> ID Card</a>}
                                                {b.guest_photo_url && <a href={getImageUrl(ensureProofPath(b.guest_photo_url))} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline flex items-center"><Camera size={16} className="mr-1" /> Photo</a>}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </SectionCard>

                        {/* Food Order History */}
                        <SectionCard title="Food Order History">
                            <table className="min-w-full text-sm">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="p-3 text-left">Order ID</th>
                                        <th className="p-3 text-left">Date</th>
                                        <th className="p-3 text-left">Room</th>
                                        <th className="p-3 text-left">Items</th>
                                        <th className="p-3 text-right">Amount</th>
                                        <th className="p-3 text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {profile.food_orders.map(o => (
                                        <tr key={o.id}>
                                            <td className="p-3">#{o.id}</td>
                                            <td className="p-3">{new Date(o.created_at).toLocaleString()}</td>
                                            <td className="p-3">{o.room_number || 'N/A'}</td>
                                            <td className="p-3">{o.items.map(i => `${i.food_item?.name || 'Unknown Item'} (x${i.quantity})`).join(', ')}</td>
                                            <td className="p-3 text-right font-semibold">₹{o.amount.toFixed(2)}</td>
                                            <td className="p-3 text-center"><span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">{o.status}</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </SectionCard>

                        {/* Service History */}
                        <SectionCard title="Service History">
                            <table className="min-w-full text-sm">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="p-3 text-left">Service ID</th>
                                        <th className="p-3 text-left">Date</th>
                                        <th className="p-3 text-left">Service</th>
                                        <th className="p-3 text-left">Room</th>
                                        <th className="p-3 text-right">Charges</th>
                                        <th className="p-3 text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {profile.services.map(s => (
                                        <tr key={s.id}>
                                            <td className="p-3">#{s.id}</td>
                                            <td className="p-3">{new Date(s.assigned_at).toLocaleString()}</td>
                                            <td className="p-3">{s.service_name}</td>
                                            <td className="p-3">{s.room_number || 'N/A'}</td>
                                            <td className="p-3 text-right font-semibold">₹{(s.charges || 0).toFixed(2)}</td>
                                            <td className="p-3 text-center"><span className={`px-2 py-1 text-xs rounded-full ${s.status === 'completed' ? 'bg-purple-100 text-purple-800' : 'bg-yellow-100 text-yellow-800'}`}>{s.status}</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </SectionCard>


                        {/* Inventory Usage Section */}
                        <SectionCard title="Inventory Usage & Amenities">
                            <table className="min-w-full text-sm">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="p-3 text-left">Date</th>
                                        <th className="p-3 text-left">Item</th>
                                        <th className="p-3 text-left">Category</th>
                                        <th className="p-3 text-left">Room</th>
                                        <th className="p-3 text-right">Quantity</th>
                                        <th className="p-3 text-right">Cost (Est.)</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {profile.inventory_usage && profile.inventory_usage.length > 0 ? (
                                        profile.inventory_usage.map((usage, idx) => (
                                            <tr key={idx}>
                                                <td className="p-3">{new Date(usage.issue_date).toLocaleString()}</td>
                                                <td className="p-3 font-medium text-gray-900">{usage.item_name}</td>
                                                <td className="p-3"><span className="px-2 py-1 bg-gray-100 rounded-full text-xs">{usage.category || 'N/A'}</span></td>
                                                <td className="p-3">{usage.room_number}</td>
                                                <td className="p-3 text-right font-semibold">{usage.quantity} {usage.unit}</td>
                                                <td className="p-3 text-right text-gray-500">₹{usage.cost ? usage.cost.toFixed(2) : '0.00'}</td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="6" className="p-4 text-center text-gray-500 italic">No inventory consumption recorded.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </SectionCard>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
};

export default GuestProfile;