import React, { useState, useEffect, useMemo, useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Icosahedron, Edges } from '@react-three/drei';
import * as THREE from 'three';

// --- Configuration ---
const API_BASE_URL = 'http://127.0.0.1:8000';

// --- Helper Components ---
const SearchIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
    </svg>
);

const UserIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-10 w-10 text-white">
        <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
        <circle cx="12" cy="7" r="4"></circle>
    </svg>
);

const ShoppingBagIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 text-gray-400">
        <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"></path>
        <path d="M3 6h18"></path>
        <path d="M16 10a4 4 0 0 1-8 0"></path>
    </svg>
);

// --- 3D Scene Component ---
const Scene = () => {
    const groupRef = useRef();
    const mouse = useRef([0, 0]);

    useFrame(({ clock }) => {
        if (groupRef.current) {
            // FIX: The animation logic was corrected to prevent conflicting updates.
            // Smoothly interpolate the x rotation based on the mouse's y position.
            groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, mouse.current[1] * 0.2, 0.02);
            
            // The target y rotation combines the continuous spin with the mouse's x position.
            const targetYRotation = -mouse.current[0] * 0.2 + clock.getElapsedTime() * 0.05;
            groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, targetYRotation, 0.02);
        }
    });

    return (
        <Canvas 
            camera={{ position: [0, 0, 5], fov: 75 }}
            onPointerMove={(e) => (mouse.current = [e.clientX / window.innerWidth - 0.5, e.clientY / window.innerHeight - 0.5])}
            className="!fixed !inset-0 !-z-10"
        >
            <ambientLight intensity={0.2} />
            <directionalLight position={[10, 10, 5]} intensity={1} />
            <group ref={groupRef}>
                <Icosahedron args={[2.5, 0]}>
                    <meshStandardMaterial color="#8A2BE2" wireframe={false} transparent opacity={0.1} />
                    <Edges scale={1} threshold={15} color="#8A2BE2" />
                </Icosahedron>
            </group>
        </Canvas>
    );
};


// --- Main Application Component ---
export default function App() {
    const [customers, setCustomers] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchAllCustomerData = async () => {
            try {
                // Fetch the list of customers first
                const listResponse = await fetch(`${API_BASE_URL}/customers?page=1&per_page=150`);
                if (!listResponse.ok) throw new Error(`API List Error: ${listResponse.status} ${listResponse.statusText}`);
                const listData = await listResponse.json();

                // FIX: Added a guard to ensure the API response is in the expected format before processing.
                if (!listData || !Array.isArray(listData.data)) {
                    throw new Error("Invalid API response: 'data' array not found.");
                }

                // Then, fetch the order_count for each customer in parallel
                const detailPromises = listData.data.map(customer =>
                    fetch(`${API_BASE_URL}/customers/${customer.id}`).then(res => {
                        if (!res.ok) { // Check each detail response as well
                           throw new Error(`Failed to fetch details for customer ${customer.id}`);
                        }
                        return res.json();
                    })
                );
                
                const customersWithDetails = await Promise.all(detailPromises);
                setCustomers(customersWithDetails);
                setError(null);
            } catch (err) {
                console.error("Fetch error:", err);
                setError(err.message);
                setCustomers([]);
            } finally {
                setLoading(false);
            }
        };

        fetchAllCustomerData();
    }, []);

    const filteredCustomers = useMemo(() => {
        if (!searchTerm) return customers;
        return customers.filter(c =>
            `${c.first_name} ${c.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
            c.email.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }, [customers, searchTerm]);

    return (
        <div className="bg-[#111111] min-h-screen font-sans text-white relative overflow-hidden">
            <Suspense fallback={null}><Scene /></Suspense>
            
            <div className="relative z-10 container mx-auto p-4 sm:p-6 lg:p-8">
                <header className="text-center my-12">
                    <h1 className="text-5xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-500 mb-2">
                        Customer Insights
                    </h1>
                    <p className="text-lg text-gray-400">A modern dashboard for e-commerce analytics.</p>
                </header>

                <div className="relative mb-10 max-w-2xl mx-auto">
                    <SearchIcon />
                    <input
                        type="text"
                        placeholder="Search by name or email..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-12 pr-4 py-3 bg-gray-900/50 border border-gray-700 rounded-full shadow-lg backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all duration-300"
                    />
                </div>

                <main>
                    {loading && <LoadingSpinner />}
                    {error && <ErrorMessage message={error} />}
                    {!loading && !error && (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {filteredCustomers.length > 0 ? (
                                filteredCustomers.map(customer => (
                                    <CustomerCard key={customer.id} customer={customer} />
                                ))
                            ) : (
                                <NoResultsFound />
                            )}
                        </div>
                    )}
                </main>
                
                <footer className="text-center mt-16 text-gray-600">
                    <p>Milestone 4: Interactive Frontend</p>
                </footer>
            </div>
        </div>
    );
}

// --- Child Components ---
const CustomerCard = React.memo(({ customer }) => (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-lg border border-white/20 overflow-hidden transition-all duration-300 hover:border-purple-400 hover:scale-105 transform">
        <div className="p-6">
            <div className="flex flex-col items-center text-center mb-4">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center mb-4 shadow-lg">
                    <UserIcon />
                </div>
                <h3 className="text-xl font-bold text-white truncate w-full" title={`${customer.first_name} ${customer.last_name}`}>
                    {customer.first_name} {customer.last_name}
                </h3>
                <p className="text-sm text-gray-400 truncate w-full" title={customer.email}>{customer.email}</p>
            </div>
            
            <div className="border-t border-white/20 my-4"></div>

            <div className="flex justify-between items-center text-gray-300">
                <div className="flex items-center space-x-2">
                    <ShoppingBagIcon />
                    <span>Orders</span>
                </div>
                <span className="font-bold text-lg text-white">{customer.order_count}</span>
            </div>
        </div>
    </div>
));

const LoadingSpinner = () => (
    <div className="flex justify-center items-center p-20">
        <div className="w-16 h-16 border-4 border-dashed rounded-full animate-spin border-purple-500"></div>
    </div>
);

const ErrorMessage = ({ message }) => (
    <div className="max-w-2xl mx-auto bg-red-900/50 border border-red-500 text-red-300 px-4 py-3 rounded-lg text-center" role="alert">
        <strong className="font-bold block">API Connection Error</strong>
        <span className="block sm:inline">Could not fetch data. Please ensure the backend is running.</span>
        <p className="text-sm mt-2 text-red-400">Details: {message}</p>
    </div>
);

const NoResultsFound = () => (
    <div className="col-span-full text-center py-16 bg-white/5 backdrop-blur-sm rounded-lg">
        <h3 className="text-2xl font-semibold text-white">No Customers Found</h3>
        <p className="text-gray-400 mt-2">Your search did not match any customer records.</p>
    </div>
);
