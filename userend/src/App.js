import React, { useState, useEffect, useRef, useMemo, useCallback, memo } from "react";
import localLogo from "./assets/logo.jpeg";
// Lucide React is used for elegant icons
import { BedDouble, Coffee, ConciergeBell, Package, ChevronRight, ChevronLeft, ChevronDown, Image as ImageIcon, Star, Quote, ChevronUp, MessageSquare, Send, X, Facebook, Instagram, Linkedin, Twitter, Moon, Sun, Droplet, Menu } from 'lucide-react';
import { SiGooglemaps } from "react-icons/si";
// Currency formatting utility
import { formatCurrency } from './utils/currency';
// API base URL utility
import { getApiBaseUrl, getMediaBaseUrl } from './utils/env';

// Custom hook to detect if an element is in the viewport
const useOnScreen = (ref, rootMargin = "0px") => {
    const [isIntersecting, setIntersecting] = useState(false);
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                setIntersecting(entry.isIntersecting);
            },
            { rootMargin }
        );
        const currentRef = ref.current;
        if (currentRef) {
            observer.observe(currentRef);
        }
        return () => {
            if (currentRef) {
                observer.unobserve(currentRef);
            }
        };
    }, [ref, rootMargin]);
    return isIntersecting;
};

// Define the themes with a consistent structure for easy switching
const themes = {
    dark: {
        id: 'dark',
        name: 'Dark',
        icon: <Moon className="w-5 h-5" />,
        bgPrimary: "bg-black",
        bgSecondary: "bg-neutral-950",
        bgCard: "bg-white",
        textPrimary: "text-white",
        textSecondary: "text-neutral-400",
        textCardPrimary: "text-neutral-900",
        textCardSecondary: "text-neutral-600",
        textAccent: "text-amber-400",
        textCardAccent: "text-amber-600",
        textTitleGradient: "from-gray-200 via-white to-gray-400",
        border: "border-neutral-700",
        cardBorder: "border-neutral-200",
        borderHover: "hover:border-amber-500/50",
        buttonBg: "bg-amber-500",
        buttonText: "text-neutral-950",
        buttonHover: "hover:bg-amber-400",
        placeholderBg: "bg-neutral-800",
        placeholderText: "text-neutral-400",
        chatBg: "bg-neutral-900",
        chatHeaderBg: "bg-neutral-800",
        chatInputBorder: "border-neutral-700",
        chatInputBg: "bg-neutral-700",
        chatInputPlaceholder: "placeholder-neutral-400",
        chatUserBg: "bg-amber-500",
        chatUserText: "text-neutral-950",
        chatModelBg: "bg-neutral-800",
        chatModelText: "text-neutral-100",
        chatLoaderBg: "bg-neutral-400",
    },
    light: {
        id: 'light',
        name: 'Light',
        icon: <Sun className="w-5 h-5" />,
        bgPrimary: "bg-neutral-50",
        bgSecondary: "bg-neutral-200",
        bgCard: "bg-white",
        textPrimary: "text-neutral-900",
        textSecondary: "text-neutral-600",
        textCardPrimary: "text-neutral-900",
        textCardSecondary: "text-neutral-600",
        textAccent: "text-amber-600",
        textCardAccent: "text-amber-600",
        cardBorder: "border-neutral-300",
        textTitleGradient: "from-amber-600 via-amber-700 to-neutral-900",
        border: "border-neutral-300",
        borderHover: "hover:border-amber-500/50",
        buttonBg: "bg-gradient-to-r from-amber-500 to-amber-600",
        buttonText: "text-white",
        buttonHover: "hover:from-amber-400 hover:to-amber-500",
        placeholderBg: "bg-neutral-100",
        placeholderText: "text-neutral-500",
        chatBg: "bg-white",
        chatHeaderBg: "bg-neutral-100",
        chatInputBorder: "border-neutral-200",
        chatInputBg: "bg-neutral-100",
        chatInputPlaceholder: "placeholder-neutral-500",
        chatUserBg: "bg-gradient-to-r from-amber-500 to-amber-600",
        chatUserText: "text-white",
        chatModelBg: "bg-neutral-100",
        chatModelText: "text-neutral-900",
        chatLoaderBg: "bg-neutral-600",
    },
    ocean: {
        id: 'ocean',
        name: 'Ocean',
        icon: <Droplet className="w-5 h-5" />,
        bgPrimary: "bg-slate-50",
        bgSecondary: "bg-slate-100",
        bgCard: "bg-neutral-50",
        textPrimary: "text-slate-900",
        textSecondary: "text-slate-600",
        textAccent: "text-teal-600",
        textTitleGradient: "from-teal-700 via-cyan-700 to-blue-800",
        border: "border-slate-300",
        borderHover: "hover:border-teal-500/50",
        buttonBg: "bg-gradient-to-r from-teal-500 to-cyan-600",
        buttonText: "text-white",
        buttonHover: "hover:from-teal-400 hover:to-cyan-500",
        placeholderBg: "bg-slate-100",
        placeholderText: "text-slate-500",
        chatBg: "bg-white",
        chatHeaderBg: "bg-slate-100",
        chatInputBorder: "border-slate-200",
        chatInputBg: "bg-slate-100",
        chatInputPlaceholder: "placeholder-slate-500",
        chatUserBg: "bg-gradient-to-r from-teal-500 to-cyan-600",
        chatUserText: "text-white",
        chatModelBg: "bg-slate-100",
        chatModelText: "text-slate-900",
        chatLoaderBg: "bg-slate-600",
    },
    forest: {
        id: 'forest',
        name: 'Forest',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-tree-pine"><path d="M17 19h2c.5 0 1-.5 1-1V9c0-2-3-3-3-3H8c-3 0-4 1.5-4 4.5v3.5c0 1.5 1 2 2 2h2" /><path d="M14 15v.5" /><path d="M13 14v.5" /><path d="M12 13v.5" /><path d="M11 12v.5" /><path d="M10 11v.5" /><path d="M9 10v.5" /><path d="M8 9v.5" /><path d="M17 14v.5" /><path d="M16 13v.5" /><path d="M15 12v.5" /><path d="M14 11v.5" /><path d="M13 10v.5" /><path d="M12 9v.5" /><path d="M11 8v.5" /><path d="M10 7v.5" /><path d="M9 6v.5" /><path d="M15 18v1" /><path d="M14 17v1" /><path d="M13 16v1" /><path d="M12 15v1" /><path d="M11 14v1" /><path d="M10 13v1" /><path d="M9 12v1" /><path d="M8 11v1" /><path d="M7 10v1" /><path d="M6 9v1" /><path d="M18 17v1" /><path d="M17 16v1" /><path d="M16 15v1" /><path d="M15 14v1" /><path d="M14 13v1" /><path d="M13 12v1" /><path d="M12 11v1" /><path d="M11 10v1" /><path d="M10 9v1" /><path d="M19 18v1" /><path d="M18 17v1" /><path d="M17 16v1" /><path d="M16 15v1" /><path d="M15 14v1" /><path d="M14 13v1" /><path d="M13 12v1" /><path d="M22 19v2" /><path d="M20 18v1" /><path d="M18 17v1" /><path d="M16 16v1" /><path d="M14 15v1" /><path d="M12 14v1" /><path d="M10 13v1" /><path d="M8 12v1" /><path d="M6 11v1" /><path d="M4 10v1" /><path d="M2 9v1" /><path d="M2 21h20" /><path d="m14 12-2-4-2 4" /><path d="m13 8-1-4-1 4" /><path d="M14 12c.5-1 1.5-2 2.5-3" /><path d="M10 12c-.5-1-1.5-2-2.5-3" /><path d="M12 22v-8" /><path d="m10 16-2 3" /><path d="m14 16 2 3" /></svg>,
        bgPrimary: "bg-green-50",
        bgSecondary: "bg-green-100",
        bgCard: "bg-neutral-50",
        textPrimary: "text-green-900",
        textSecondary: "text-green-600",
        textAccent: "text-emerald-600",
        textTitleGradient: "from-emerald-700 via-green-700 to-teal-800",
        border: "border-green-300",
        borderHover: "hover:border-emerald-500/50",
        buttonBg: "bg-gradient-to-r from-emerald-500 to-green-600",
        buttonText: "text-white",
        buttonHover: "hover:from-emerald-400 hover:to-green-500",
        placeholderBg: "bg-green-100",
        placeholderText: "text-green-500",
        chatBg: "bg-white",
        chatHeaderBg: "bg-green-100",
        chatInputBorder: "border-green-200",
        chatInputBg: "bg-green-100",
        chatInputPlaceholder: "placeholder-green-500",
        chatUserBg: "bg-gradient-to-r from-emerald-500 to-green-600",
        chatUserText: "text-white",
        chatModelBg: "bg-green-100",
        chatModelText: "text-green-900",
        chatLoaderBg: "bg-green-600",
    },
    rose: {
        id: 'rose',
        name: 'Rose',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-flower"><path d="M12 7.5a4.5 4.5 0 1 1 4.5 4.5H12a4.5 4.5 0 1 1-4.5-4.5H12z" /><path d="M12 12a4.5 4.5 0 1 1 4.5 4.5H12a4.5 4.5 0 1 1-4.5-4.5H12z" /><path d="M12 12a4.5 4.5 0 1 1-4.5-4.5H12a4.5 4.5 0 1 1 4.5 4.5H12z" /><path d="M12 12a4.5 4.5 0 1 1 4.5 4.5H12a4.5 4.5 0 1 1-4.5-4.5H12z" /><path d="M7.5 12H12a4.5 4.5 0 0 0 4.5-4.5v-3a4.5 4.5 0 1 1 0 9v3a4.5 4.5 0 1 1 0-9h-4.5a4.5 4.5 0 0 0-4.5 4.5V12z" /></svg>,
        bgPrimary: "bg-pink-50",
        bgSecondary: "bg-pink-100",
        bgCard: "bg-neutral-50",
        textPrimary: "text-pink-900",
        textSecondary: "text-pink-600",
        textAccent: "text-rose-600",
        textTitleGradient: "from-rose-700 via-pink-700 to-fuchsia-800",
        border: "border-pink-300",
        borderHover: "hover:border-rose-500/50",
        buttonBg: "bg-gradient-to-r from-rose-500 to-pink-600",
        buttonText: "text-white",
        buttonHover: "hover:from-rose-400 hover:to-pink-500",
        placeholderBg: "bg-pink-100",
        placeholderText: "text-pink-500",
        chatBg: "bg-white",
        chatHeaderBg: "bg-pink-100",
        chatInputBorder: "border-pink-200",
        chatInputBg: "bg-pink-100",
        chatInputPlaceholder: "placeholder-pink-500",
        chatUserBg: "bg-gradient-to-r from-rose-500 to-pink-600",
        chatUserText: "text-white",
        chatModelBg: "bg-pink-100",
        chatModelText: "text-pink-900",
        chatLoaderBg: "bg-pink-600",
    },
    slate: {
        id: 'slate',
        name: 'Slate',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-cloud"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242" /></svg>,
        bgPrimary: "bg-gray-950",
        bgSecondary: "bg-gray-900",
        bgCard: "bg-neutral-50",
        textPrimary: "text-gray-100",
        textSecondary: "text-gray-400",
        textAccent: "text-sky-400",
        textTitleGradient: "from-gray-200 via-gray-400 to-gray-600",
        border: "border-gray-700",
        borderHover: "hover:border-sky-400/50",
        buttonBg: "bg-sky-500",
        buttonText: "text-gray-950",
        buttonHover: "hover:bg-sky-400",
        placeholderBg: "bg-gray-800",
        placeholderText: "text-gray-400",
        chatBg: "bg-gray-900",
        chatHeaderBg: "bg-gray-800",
        chatInputBorder: "border-gray-700",
        chatInputBg: "bg-gray-700",
        chatInputPlaceholder: "placeholder-gray-400",
        chatUserBg: "bg-sky-500",
        chatUserText: "text-gray-950",
        chatModelBg: "bg-gray-800",
        chatModelText: "text-gray-100",
        chatLoaderBg: "bg-gray-400",
    },
    sunrise: {
        id: 'sunrise',
        name: 'Sunrise',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-sunrise"><path d="M12 2v2" /><path d="m5 10 1-1" /><path d="m19 10 1-1" /><path d="M12 16a6 6 0 0 0 0 12" /><path d="m3 16 1-1" /><path d="m21 16-1-1" /><path d="m8 20 2-2" /><path d="m16 20-2-2" /></svg>,
        bgPrimary: "bg-orange-50",
        bgSecondary: "bg-yellow-100",
        bgCard: "bg-neutral-50",
        textPrimary: "text-orange-900",
        textSecondary: "text-orange-600",
        textAccent: "text-red-500",
        textTitleGradient: "from-orange-500 via-yellow-600 to-red-700",
        border: "border-yellow-200",
        borderHover: "hover:border-red-500/50",
        buttonBg: "bg-red-500",
        buttonText: "text-white",
        buttonHover: "hover:bg-red-400",
        placeholderBg: "bg-yellow-50",
        placeholderText: "text-orange-400",
        chatBg: "bg-white",
        chatHeaderBg: "bg-yellow-100",
        chatInputBorder: "border-yellow-200",
        chatInputBg: "bg-yellow-100",
        chatInputPlaceholder: "placeholder-orange-500",
        chatUserBg: "bg-red-500",
        chatUserText: "text-white",
        chatModelBg: "bg-yellow-100",
        chatModelText: "text-orange-900",
        chatLoaderBg: "bg-red-600",
    },
    lavender: {
        id: 'lavender',
        name: 'Lavender',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-lavender"><path d="M14.5 16.5c-2.4-1-4.2-2-5.5-2.5-1.5-.5-3.6-1-4.5-2-.8-1-1.3-2.2-1-3.5C3.3 6.7 4 6 5 6c1.1 0 2.4.8 3.5 2.5 1.2 1.9 2 4.2 2.5 5.5.5 1.5 1 3.6 2 4.5 1 .8 2.2 1.3 3.5 1C17.3 17.3 18 16.6 18 15.6c0-1.1-.8-2.4-2.5-3.5-1.9-1.2-4.2-2-5.5-2.5-1.5-.5-3.6-1-4.5-2-.8-1-1.3-2.2-1-3.5.3-1.3 1-2 2-2 1.1 0 2.4.8 3.5 2.5 1.9 1.2 4.2 2 5.5 2.5 1.5.5 3.6 1 4.5 2 .8 1 1.3 2.2 1 3.5-.3 1.3-1 2-2 2-1.1 0-2.4-.8-3.5-2.5-1.9-1.2-4.2-2-5.5-2.5-1.5-.5-3.6-1-4.5-2-.8-1-1.3-2.2-1-3.5-.3-1.3-1-2-2-2-1.1 0-2.4-.8-3.5-2.5" /><path d="M12 12c-2.4-1-4.2-2-5.5-2.5-1.5-.5-3.6-1-4.5-2-.8-1-1.3-2.2-1-3.5.3-1.3 1-2 2-2 1.1 0 2.4.8 3.5 2.5 1.9 1.2 4.2 2 5.5 2.5 1.5.5 3.6 1 4.5 2 .8 1 1.3 2.2 1 3.5-.3 1.3-1 2-2 2-1.1 0-2.4-.8-3.5-2.5-1.9-1.2-4.2-2-5.5-2.5-1.5-.5-3.6-1-4.5-2-.8-1-1.3-2.2-1-3.5-.3-1.3-1-2-2-2-1.1 0-2.4-.8-3.5-2.5" /></svg>,
        bgPrimary: "bg-indigo-950",
        bgSecondary: "bg-indigo-900",
        bgCard: "bg-neutral-50",
        textPrimary: "text-indigo-100",
        textSecondary: "text-indigo-300",
        textAccent: "text-violet-400",
        textTitleGradient: "from-indigo-200 via-violet-300 to-purple-400",
        border: "border-indigo-700",
        borderHover: "hover:border-violet-400/50",
        buttonBg: "bg-violet-500",
        buttonText: "text-indigo-950",
        buttonHover: "hover:bg-violet-400",
        placeholderBg: "bg-indigo-800",
        placeholderText: "text-indigo-400",
        chatBg: "bg-indigo-900",
        chatHeaderBg: "bg-indigo-800",
        chatInputBorder: "border-indigo-700",
        chatInputBg: "bg-indigo-700",
        chatInputPlaceholder: "placeholder-indigo-400",
        chatUserBg: "bg-violet-500",
        chatUserText: "text-indigo-950",
        chatModelBg: "bg-indigo-800",
        chatModelText: "text-indigo-100",
        chatLoaderBg: "bg-indigo-400",
    },
    desert: {
        id: 'desert',
        name: 'Desert',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-sunrise"><path d="M12 2v2" /><path d="m5 10 1-1" /><path d="m19 10 1-1" /><path d="M12 16a6 6 0 0 0 0 12" /><path d="m3 16 1-1" /><path d="m21 16-1-1" /><path d="m8 20 2-2" /><path d="m16 20-2-2" /></svg>,
        bgPrimary: "bg-stone-100",
        bgSecondary: "bg-stone-200",
        bgCard: "bg-neutral-50",
        textPrimary: "text-stone-900",
        textSecondary: "text-stone-600",
        textAccent: "text-orange-700",
        textTitleGradient: "from-stone-700 via-stone-900 to-amber-900",
        border: "border-stone-300",
        borderHover: "hover:border-orange-700/50",
        buttonBg: "bg-orange-700",
        buttonText: "text-white",
        buttonHover: "hover:bg-orange-600",
        placeholderBg: "bg-stone-50",
        placeholderText: "text-stone-500",
        chatBg: "bg-white",
        chatHeaderBg: "bg-stone-100",
        chatInputBorder: "border-stone-200",
        chatInputBg: "bg-stone-100",
        chatInputPlaceholder: "placeholder-stone-500",
        chatUserBg: "bg-orange-700",
        chatUserText: "text-white",
        chatModelBg: "bg-stone-100",
        chatModelText: "text-stone-900",
        chatLoaderBg: "bg-stone-600",
    },
    resort: {
        id: 'resort',
        name: 'Resort',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-sun"><path d="M12 2v2" /><path d="m5 10 1-1" /><path d="m19 10-1-1" /><path d="M12 16a6 6 0 0 0 0 12" /><path d="m3 16 1-1" /><path d="m21 16-1-1" /><path d="m8 20 2-2" /><path d="m16 20-2-2" /></svg>,
        bgPrimary: "bg-white",
        bgSecondary: "bg-orange-50",
        bgCard: "bg-white",
        textPrimary: "text-orange-900",
        textSecondary: "text-orange-700",
        textAccent: "text-amber-600",
        textCardPrimary: "text-orange-900",
        textCardSecondary: "text-orange-600",
        textCardAccent: "text-amber-700",
        textTitleGradient: "from-amber-600 via-orange-600 to-amber-800",
        border: "border-orange-200",
        cardBorder: "border-orange-100",
        borderHover: "hover:border-amber-500/60",
        buttonBg: "bg-gradient-to-r from-amber-500 to-orange-600",
        buttonText: "text-white",
        buttonHover: "hover:from-amber-400 hover:to-orange-500",
        placeholderBg: "bg-orange-50",
        placeholderText: "text-orange-400",
        chatBg: "bg-white",
        chatHeaderBg: "bg-orange-50",
        chatInputBorder: "border-orange-200",
        chatInputBg: "bg-orange-50",
        chatInputPlaceholder: "placeholder-orange-400",
        chatUserBg: "bg-gradient-to-r from-amber-500 to-orange-600",
        chatUserText: "text-white",
        chatModelBg: "bg-orange-50",
        chatModelText: "text-orange-900",
        chatLoaderBg: "bg-amber-500",
    },
    grape: {
        id: 'grape',
        name: 'Grape',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-grape"><path d="M22 6c0 4-4 8-10 8S2 10 2 6" /><path d="M12 14c-6 0-10 4-10 8s4 8 10 8" /><path d="M22 14c-6 0-10 4-10 8s4 8 10 8" /></svg>,
        bgPrimary: "bg-purple-950",
        bgSecondary: "bg-purple-900",
        bgCard: "bg-neutral-50",
        textPrimary: "text-purple-100",
        textSecondary: "text-purple-300",
        textAccent: "text-pink-400",
        textTitleGradient: "from-purple-200 via-pink-300 to-fuchsia-400",
        border: "border-purple-700",
        borderHover: "hover:border-pink-400/50",
        buttonBg: "bg-pink-500",
        buttonText: "text-purple-950",
        buttonHover: "hover:bg-pink-400",
        placeholderBg: "bg-purple-800",
        placeholderText: "text-purple-400",
        chatBg: "bg-purple-900",
        chatHeaderBg: "bg-purple-800",
        chatInputBorder: "border-purple-700",
        chatInputBg: "bg-purple-700",
        chatInputPlaceholder: "placeholder-purple-400",
        chatUserBg: "bg-pink-500",
        chatUserText: "text-purple-950",
        chatModelBg: "bg-purple-800",
        chatModelText: "text-purple-100",
        chatLoaderBg: "bg-purple-400",
    },
    sky: {
        id: 'sky',
        name: 'Sky',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-cloud-sun"><path d="M12 2v2" /><path d="m4.9 10 1-1" /><path d="m19.1 10-1-1" /><path d="M14 16a6 6 0 0 0 0 12" /><path d="m3 16 1-1" /><path d="m21 16-1-1" /><path d="m8 20 2-2" /><path d="m16 20-2-2" /></svg>,
        bgPrimary: "bg-sky-50",
        bgSecondary: "bg-sky-100",
        bgCard: "bg-neutral-50",
        textPrimary: "text-sky-900",
        textSecondary: "text-sky-600",
        textAccent: "text-blue-500",
        textTitleGradient: "from-sky-700 via-blue-800 to-indigo-900",
        border: "border-sky-300",
        borderHover: "hover:border-blue-500/50",
        buttonBg: "bg-blue-500",
        buttonText: "text-white",
        buttonHover: "hover:bg-blue-400",
        placeholderBg: "bg-sky-50",
        placeholderText: "text-sky-500",
        chatBg: "bg-white",
        chatHeaderBg: "bg-sky-100",
        chatInputBorder: "border-sky-200",
        chatInputBg: "bg-sky-100",
        chatInputPlaceholder: "placeholder-sky-500",
        chatUserBg: "bg-blue-500",
        chatUserText: "text-white",
        chatModelBg: "bg-sky-100",
        chatModelText: "text-sky-900",
        chatLoaderBg: "bg-blue-600",
    },
    fire: {
        id: 'fire',
        name: 'Fire',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-flame"><path d="M18 10c-1.2-1.2-3-2-5-2-1.2 0-2.8.8-4 2-1.2 1.2-2 3-2 5-2.2 2.2-2.5 4.5-2.5 5.5s.8 1.5 1.5 1.5c.7 0 1.5-.8 1.5-1.5s.3-3.3 2.5-5.5c1.2-1.2 3-2 5-2 1.2 0 2.8.8 4 2 1.2 1.2 2 3 2 5 2.2 2.2 2.5 4.5 2.5 5.5s-.8 1.5-1.5 1.5c-.7 0-1.5-.8-1.5-1.5s-.3-3.3-2.5-5.5z" /></svg>,
        bgPrimary: "bg-red-950",
        bgSecondary: "bg-red-900",
        bgCard: "bg-neutral-50",
        textPrimary: "text-red-100",
        textSecondary: "text-red-300",
        textAccent: "text-orange-400",
        textTitleGradient: "from-orange-200 via-orange-300 to-yellow-400",
        border: "border-red-700",
        borderHover: "hover:border-orange-400/50",
        buttonBg: "bg-orange-500",
        buttonText: "text-red-950",
        buttonHover: "hover:bg-orange-400",
        placeholderBg: "bg-red-800",
        placeholderText: "text-red-400",
        chatBg: "bg-red-900",
        chatHeaderBg: "bg-red-800",
        chatInputBorder: "border-red-700",
        chatInputBg: "bg-red-700",
        chatInputPlaceholder: "placeholder-red-400",
        chatUserBg: "bg-orange-500",
        chatUserText: "text-red-950",
        chatModelBg: "bg-red-800",
        chatModelText: "text-red-100",
        chatLoaderBg: "bg-red-400",
    },
    mint: {
        id: 'mint',
        name: 'Mint',
        icon: <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-leaf"><path d="M2 13c3.5-3.5 12-5 18 0 0 0-4 4-8 8s-8-4-10-6z" /></svg>,
        bgPrimary: "bg-teal-50",
        bgSecondary: "bg-teal-100",
        bgCard: "bg-neutral-50",
        textPrimary: "text-teal-900",
        textSecondary: "text-teal-600",
        textAccent: "text-emerald-600",
        textTitleGradient: "from-teal-700 via-emerald-900 to-green-900",
        border: "border-teal-200",
        borderHover: "hover:border-emerald-600/50",
        buttonBg: "bg-emerald-600",
        buttonText: "text-white",
        buttonHover: "hover:bg-emerald-500",
        placeholderBg: "bg-teal-50",
        placeholderText: "text-teal-500",
        chatBg: "bg-white",
        chatHeaderBg: "bg-teal-100",
        chatInputBorder: "border-teal-200",
        chatInputBg: "bg-teal-100",
        chatInputPlaceholder: "placeholder-teal-500",
        chatUserBg: "bg-emerald-600",
        chatUserText: "text-white",
        chatModelBg: "bg-teal-100",
        chatModelText: "text-teal-900",
        chatLoaderBg: "bg-teal-600",
    },

};

// Background animation component for the floating bubbles
const BackgroundAnimation = ({ theme }) => {
    const bubbles = Array.from({ length: 30 }, (_, i) => { // Reduced bubble count for a smoother, more elegant effect
        const size = `${2 + Math.random() * 4}rem`;
        const animationDelay = `${Math.random() * 20}s`;
        const animationDuration = `${25 + Math.random() * 25}s`; // Longer duration for a calmer float
        const opacity = 0.1 + Math.random() * 0.15; // Reduced max opacity for a more subtle look

        let bubbleColor = "";
        switch (theme.id) {
            case 'dark': bubbleColor = "bg-white/20"; break;
            case 'light': bubbleColor = "bg-neutral-400"; break;
            case 'ocean': bubbleColor = "bg-cyan-400"; break;
            case 'forest': bubbleColor = "bg-lime-400"; break;
            case 'rose': bubbleColor = "bg-fuchsia-400"; break;
            case 'slate': bubbleColor = "bg-sky-400"; break;
            case 'sunrise': bubbleColor = "bg-red-400"; break;
            case 'lavender': bubbleColor = "bg-violet-400"; break;
            case 'desert': bubbleColor = "bg-orange-400"; break;
            case 'grape': bubbleColor = "bg-pink-400"; break;
            case 'sky': bubbleColor = "bg-blue-400"; break;
            case 'fire': bubbleColor = "bg-yellow-400"; break;
            case 'mint': bubbleColor = "bg-emerald-400"; break;
            default: bubbleColor = "bg-neutral-400";
        }

        const direction = Math.floor(Math.random() * 4);
        let style = {
            width: size,
            height: size,
            animationDelay,
            animationDuration,
            opacity,
        };
        let animationClass = "";

        switch (direction) {
            case 0: // from bottom to top
                style.bottom = '-10%';
                style.left = `${Math.random() * 100}%`;
                animationClass = 'bubble-up';
                break;
            case 1: // from left to right
                style.left = '-10%';
                style.top = `${Math.random() * 100}%`;
                animationClass = 'bubble-right';
                break;
            case 2: // from top to bottom
                style.top = '-10%';
                style.left = `${Math.random() * 100}%`;
                animationClass = 'bubble-down';
                break;
            case 3: // from right to left
            default:
                style.right = '-10%';
                style.top = `${Math.random() * 100}%`;
                animationClass = 'bubble-left';
                break;
        }

        return (
            <li
                key={i}
                className={`absolute rounded-full list-none block z-0 ${bubbleColor} ${animationClass}`}
                style={style}
            ></li>
        );
    });

    return (
        <>
            <style>{`
                /* Resort Golden Orange White Theme Typography & Colors */
                @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
                
                :root {
                    --font-display: 'Cormorant Garamond', serif;
                    --font-body: 'Poppins', sans-serif;
                    --color-resort-gold: #d97706;
                    --color-resort-gold-dark: #b45309;
                    --color-resort-orange: #ea580c;
                    --color-resort-amber: #f59e0b;
                    --color-resort-white: #ffffff;
                }
                
                * {
                    max-width: 100%;
                }
                
                body {
                    font-family: var(--font-body);
                    font-weight: 400;
                    letter-spacing: 0.01em;
                    background-color: var(--color-resort-white);
                    color: var(--color-resort-gold-dark);
                    overflow-x: hidden;
                }
                
                h1, h2, h3, h4, h5, h6 {
                    font-family: var(--font-display);
                    font-weight: 700;
                    letter-spacing: -0.015em;
                    max-width: 100%;
                    word-wrap: break-word;
                    color: var(--color-resort-gold-dark);
                }
                
                section {
                    width: 100%;
                    overflow-x: hidden;
                }
                
                img {
                    max-width: 100%;
                    height: auto;
                }
                
                .container-custom {
                    max-width: 95%;
                    margin-left: auto;
                    margin-right: auto;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
                
                @media (min-width: 640px) {
                    .container-custom {
                        max-width: 98%;
                        padding-left: 1.5rem;
                        padding-right: 1.5rem;
                    }
                }
                
                @media (min-width: 1024px) {
                    .container-custom {
                        max-width: 1400px;
                    }
                }
                
                /* Resort Premium Styling */
                .luxury-card {
                    border-radius: 1rem;
                    box-shadow: 0 6px 24px -8px rgba(12, 61, 38, 0.25);
                    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .luxury-card:hover {
                    box-shadow: 0 24px 40px -12px rgba(12, 61, 38, 0.35), 0 0 0 1px rgba(201, 156, 78, 0.25);
                    transform: translateY(-4px) scale(1.015);
                }
                
                .premium-gradient {
                    background: linear-gradient(135deg, #0f5132 0%, #1a7042 60%, #218051 100%);
                }
                
                .premium-text-gradient {
                    background: linear-gradient(135deg, #0f5132 0%, #1a7042 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                }
                
                .luxury-overlay {
                    background: linear-gradient(180deg, rgba(12, 61, 38, 0.05) 0%, rgba(12, 61, 38, 0.55) 55%, rgba(15, 49, 38, 0.85) 100%);
                }
                
                .section-badge {
                    display: inline-block;
                    padding: 0.5rem 1.5rem;
                    background: rgba(15, 81, 50, 0.08);
                    color: #0f5132;
                    font-weight: 600;
                    letter-spacing: 0.12em;
                    border-radius: 9999px;
                    border: 1px solid rgba(201, 156, 78, 0.35);
                    backdrop-filter: blur(10px);
                    text-transform: uppercase;
                }
                
                .luxury-shadow {
                    box-shadow: 0 28px 50px -18px rgba(12, 61, 38, 0.28), 0 0 0 1px rgba(201, 156, 78, 0.12);
                }
                
                .card-image {
                    max-height: 200px;
                    object-fit: cover;
                    filter: brightness(1) saturate(1.05);
                    transition: all 0.5s ease;
                }
                
                .luxury-card:hover .card-image {
                    filter: brightness(1.08) saturate(1.2);
                }
                
                .card-title {
                    font-size: 1.125rem;
                    margin-bottom: 0.5rem;
                    font-weight: 700;
                    letter-spacing: -0.01em;
                }
                
                .card-description {
                    font-size: 0.875rem;
                    line-height: 1.6;
                    color: #4f6f62;
                }
                
                @keyframes slow-pan { 
                    0% { transform: translate(0, 0) scale(1); }
                    50% { transform: translate(-3%, 3%) scale(1.05); }
                    100% { transform: translate(0, 0) scale(1); }
                }
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(30px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                
                @keyframes fade-in-up {
                    0% { opacity: 0; transform: translateY(40px); }
                    100% { opacity: 1; transform: translateY(0); }
                }
                
                @keyframes slide-in-left {
                    0% { opacity: 0; transform: translateX(-50px); }
                    100% { opacity: 1; transform: translateX(0); }
                }
                
                @keyframes slide-in-right {
                    0% { opacity: 0; transform: translateX(50px); }
                    100% { opacity: 1; transform: translateX(0); }
                }
                
                @keyframes float-gentle {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-10px); }
                }
                
                @keyframes bounce-gentle {
                    0%, 100% { transform: translateY(0px); }
                    50% { transform: translateY(-8px); }
                }
                
                @keyframes pulse-gentle {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.9; transform: scale(1.02); }
                }
                
                .animate-fade-in-up {
                    animation: fade-in-up 1s ease-out forwards;
                    opacity: 0;
                }
                
                .animate-slide-in-left {
                    animation: slide-in-left 1s ease-out forwards;
                    opacity: 0;
                }
                
                .animate-slide-in-right {
                    animation: slide-in-right 1s ease-out forwards;
                    opacity: 0;
                }
                
                .animate-float-gentle {
                    animation: float-gentle 3s ease-in-out infinite;
                }
                
                .animate-bounce-gentle {
                    animation: bounce-gentle 2s ease-in-out infinite;
                }
                
                @keyframes zoom-gentle {
                    0% { transform: scale(1) translate(0, 0); }
                    50% { transform: scale(1.08) translate(-2%, 2%); }
                    100% { transform: scale(1.05) translate(2%, -2%); }
                }
                
                .animate-zoom-gentle {
                    animation: zoom-gentle 30s ease-in-out infinite;
                }
                
                .animate-pulse-gentle {
                    animation: pulse-gentle 2s ease-in-out infinite;
                }

                /* Lazy reveal utility - optimized for performance */
                .reveal { opacity: 0; transform: translateY(18px) scale(.98); filter: blur(6px); will-change: opacity, transform, filter; }
                .reveal.in { opacity: 1; transform: none; filter: blur(0); transition: opacity .2s ease, transform .2s ease, filter .2s ease; }
                @keyframes gentle-glow {
                    0%, 100% { filter: brightness(1) drop-shadow(0 0 20px rgba(245, 158, 11, 0.3)); }
                    50% { filter: brightness(1.1) drop-shadow(0 0 30px rgba(245, 158, 11, 0.5)); }
                }
                @keyframes gentle-pulse {
                    0%, 100% { box-shadow: 0 10px 40px rgba(245, 158, 11, 0.3); }
                    50% { box-shadow: 0 15px 60px rgba(245, 158, 11, 0.6); }
                }
                @keyframes bubble-up { 0% { transform: translate(0, 0) rotate(0deg); } 25% { transform: translate(20px, -25vh) rotate(45deg); } 50% { transform: translate(-20px, -50vh) rotate(90deg); } 75% { transform: translate(20px, -75vh) rotate(135deg); } 100% { transform: translate(0, -110vh) rotate(180deg); } }
                @keyframes bubble-down { 0% { transform: translate(0, 0) rotate(0deg); } 25% { transform: translate(-20px, 25vh) rotate(-45deg); } 50% { transform: translate(20px, 50vh) rotate(-90deg); } 75% { transform: translate(-20px, 75vh) rotate(-135deg); } 100% { transform: translate(0, 110vh) rotate(-180deg); } }
                @keyframes bubble-left { 0% { transform: translate(0, 0) rotate(0deg); } 25% { transform: translate(-25vw, 20px) rotate(45deg); } 50% { transform: translate(-50vw, -20px) rotate(90deg); } 75% { transform: translate(-75vw, 20px) rotate(135deg); } 100% { transform: translate(-110vw, 0) rotate(180deg); } }
                @keyframes bubble-right { 0% { transform: translate(0, 0) rotate(0deg); } 25% { transform: translate(25vw, -20px) rotate(-45deg); } 50% { transform: translate(50vw, 20px) rotate(-90deg); } 75% { transform: translate(75vw, -20px) rotate(-135deg); } 100% { transform: translate(110vw, 0) rotate(-180deg); } }
                .bubble-up { animation: bubble-up ease-in-out infinite; }
                .bubble-down { animation: bubble-down ease-in-out infinite; }
                .bubble-left { animation: bubble-left ease-in-out infinite; }
                .bubble-right { animation: bubble-right ease-in-out infinite; }
            `}</style>
            <ul className="absolute top-0 left-0 w-full h-full overflow-hidden z-0">
                {bubbles}
            </ul>
        </>
    );
};

/**
 * A helper function to ensure a URL is valid for an external link.
 * It prepends "https://" if the protocol is missing.
 * @param {string} url The URL to format.
 * @returns {string} A valid, absolute URL.
 */
const formatUrl = (url) => {
    if (!url || typeof url !== 'string') return '#'; // Return a safe, non-navigating link if URL is missing
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    return `https://${url}`;
};

export default function App() {
    const [rooms, setRooms] = useState([]);
    const [allRooms, setAllRooms] = useState([]); // Store all rooms for filtering
    const [bookings, setBookings] = useState([]); // Store regular bookings for availability check
    const [packageBookings, setPackageBookings] = useState([]); // Store package bookings for availability check
    const [services, setServices] = useState([]);
    const [foodItems, setFoodItems] = useState([]);
    const [foodCategories, setFoodCategories] = useState([]);
    const logoCandidates = useMemo(() => {
        const unique = new Set();
        const candidates = [];
        const addCandidate = (src) => {
            if (!src || unique.has(src)) return;
            unique.add(src);
            candidates.push(src);
        };

        addCandidate(localLogo);

        const publicUrl = process.env.PUBLIC_URL;
        if (publicUrl && publicUrl !== ".") {
            addCandidate(`${publicUrl.replace(/\/$/, "")}/logo.jpeg`);
            addCandidate(`${publicUrl.replace(/\/$/, "")}/logo.png`);
        }

        addCandidate("/logo.jpeg");
        addCandidate("/logo.png");
        addCandidate("/orchid/logo.jpeg");
        addCandidate("/orchid/logo.png");

        if (typeof window !== "undefined") {
            const origin = window.location.origin;
            addCandidate(`${origin}/logo.jpeg`);
            addCandidate(`${origin}/logo.png`);
            addCandidate(`${origin}/orchid/logo.jpeg`);
            addCandidate(`${origin}/orchid/logo.png`);
            const { pathname } = window.location;
            if (pathname && pathname !== "/") {
                const trimmedPath = pathname.endsWith("/") ? pathname.slice(0, -1) : pathname;
                if (trimmedPath) {
                    addCandidate(`${trimmedPath}/logo.jpeg`);
                    addCandidate(`${trimmedPath}/logo.png`);
                }
                const segments = pathname.split("/").filter(Boolean);
                if (segments.length > 0) {
                    addCandidate(`/${segments[0]}/logo.jpeg`);
                    addCandidate(`/${segments[0]}/logo.png`);
                }
            }
        }

        // Logo candidates for Resort
        // addCandidate("https://resort.com/logo.jpeg");

        return candidates;
    }, []);
    const [logoIndex, setLogoIndex] = useState(0);
    const logoSrc = logoCandidates[Math.min(logoIndex, logoCandidates.length - 1)];
    const [packages, setPackages] = useState([]);
    const [resortInfo, setResortInfo] = useState(null);
    const [galleryImages, setGalleryImages] = useState([]);
    const [reviews, setReviews] = useState([]);
    const [bannerData, setBannerData] = useState([]);
    const [signatureExperiences, setSignatureExperiences] = useState([]);
    const [planWeddings, setPlanWeddings] = useState([]);
    const [nearbyAttractions, setNearbyAttractions] = useState([]);
    const [nearbyAttractionBanners, setNearbyAttractionBanners] = useState([]);
    const [currentBannerIndex, setCurrentBannerIndex] = useState(0);
    const [currentWeddingIndex, setCurrentWeddingIndex] = useState(0);
    const [currentAttractionBannerIndex, setCurrentAttractionBannerIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showBackToTop, setShowBackToTop] = useState(false);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [chatHistory, setChatHistory] = useState([
        { role: "model", parts: [{ text: "Hello! I am your personal AI Concierge. How can I assist you with your stay at the Elysian Retreat today?" }] }
    ]);
    const [userMessage, setUserMessage] = useState("");
    const [isChatLoading, setIsChatLoading] = useState(false);
    const [showAllRooms, setShowAllRooms] = useState(false);

    // Package image slider state
    const [packageImageIndex, setPackageImageIndex] = useState({});
    // Signature carousel index
    const [signatureIndex, setSignatureIndex] = useState(0);

    // Banner Message State
    const [bannerMessage, setBannerMessage] = useState({ type: null, text: "" });

    // Function to show banner message with auto-dismiss
    const showBannerMessage = (type, text) => {
        setBannerMessage({ type, text });
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            setBannerMessage({ type: null, text: "" });
        }, 5000);
    };

    // Booking Modals State
    const [isRoomBookingFormOpen, setIsRoomBookingFormOpen] = useState(false);
    const [isPackageBookingFormOpen, setIsPackageBookingFormOpen] = useState(false);
    const [isPackageSelectionOpen, setIsPackageSelectionOpen] = useState(false);
    const [isServiceBookingFormOpen, setIsServiceBookingFormOpen] = useState(false);
    const [isFoodOrderFormOpen, setIsFoodOrderFormOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isGeneralBookingOpen, setIsGeneralBookingOpen] = useState(false);
    const [showAmenities, setShowAmenities] = useState(false);

    const [bookingData, setBookingData] = useState({
        room_ids: [],
        guest_name: "",
        guest_mobile: "",
        guest_email: "",
        check_in: "",
        check_out: "",
        adults: 1,
        children: 0,
    });
    const [packageBookingData, setPackageBookingData] = useState({
        package_id: null,
        room_ids: [],
        guest_name: "",
        guest_mobile: "",
        guest_email: "",
        check_in: "",
        check_out: "",
        adults: 1,
        children: 0,
        food_preferences: "",
        special_requests: ""
    });
    const [serviceBookingData, setServiceBookingData] = useState({
        service_id: null,
        guest_name: "",
        guest_mobile: "",
        guest_email: "",
        room_id: null,
    });
    const [foodOrderData, setFoodOrderData] = useState({
        room_id: null,
        items: {},
    });

    const [bookingMessage, setBookingMessage] = useState({ type: null, text: "" });
    const [isBookingLoading, setIsBookingLoading] = useState(false);

    // Fallback: if data fetch hangs for some reason, hide the loader after 8s so the page can render.
    useEffect(() => {
        if (!loading) return;
        const timer = setTimeout(() => {
            setLoading(false);
        }, 8000);
        return () => clearTimeout(timer);
    }, [loading]);

    // Use Resort golden orange white theme palette
    const currentTheme = 'resort';
    const theme = themes[currentTheme];

    const bannerRef = useRef(null);
    const chatMessagesRef = useRef(null);
    const isBannerVisible = useOnScreen(bannerRef);

    const ITEM_PLACEHOLDER = "https://placehold.co/400x300/2d3748/cbd5e0?text=Image+Not+Available";

    // Helper function to get correct image URL
    const getImageUrl = (imagePath) => {
        if (!imagePath) return ITEM_PLACEHOLDER;
        if (imagePath.startsWith('http')) return imagePath; // Already a full URL
        const baseUrl = getMediaBaseUrl(); // e.g. http://localhost:8011

        // Ensure the path starts with / but don't strip /uploads/
        // The backend serves images at /uploads/... so we must keep that prefix
        const cleanPath = imagePath.startsWith('/') ? imagePath : `/${imagePath}`;

        return `${baseUrl}${cleanPath}`;
    };

    const activeSignatureExperiences = useMemo(
        () => signatureExperiences.filter(exp => exp.is_active && exp.image_url),
        [signatureExperiences]
    );
    const totalSignatureExperiences = activeSignatureExperiences.length;
    const activeNearbyAttractions = useMemo(
        () => nearbyAttractions.filter(attraction => attraction.is_active),
        [nearbyAttractions]
    );
    const totalNearbyAttractions = activeNearbyAttractions.length;
    const activeNearbyAttractionBanners = useMemo(
        () => nearbyAttractionBanners.filter(banner => banner.is_active),
        [nearbyAttractions]
    );
    const totalNearbyAttractionBanners = activeNearbyAttractionBanners.length;

    const foodItemsByCategory = useMemo(() => {
        if (!foodItems || !foodItems.length) return {};
        return foodItems.reduce((acc, item) => {
            const categoryName = item.category?.name || item.category_name || "Uncategorized";
            if (!acc[categoryName]) acc[categoryName] = [];
            acc[categoryName].push(item);
            return acc;
        }, {});
    }, [foodItems]);
    const categoryNames = useMemo(() => {
        const fromCategories = foodCategories.map(cat => cat.name || "Uncategorized");
        const fromItems = Object.keys(foodItemsByCategory);
        return Array.from(new Set(['All', ...fromCategories, ...fromItems]));
    }, [foodCategories, foodItemsByCategory]);
    const [selectedFoodCategory, setSelectedFoodCategory] = useState('All');
    useEffect(() => {
        if (!categoryNames.length) {
            if (selectedFoodCategory !== 'All') setSelectedFoodCategory('All');
            return;
        }
        if (!categoryNames.includes(selectedFoodCategory)) {
            setSelectedFoodCategory(categoryNames[0]);
        }
    }, [categoryNames, selectedFoodCategory]);
    useEffect(() => {
        if (!categoryNames.includes(selectedFoodCategory)) {
            setSelectedFoodCategory(categoryNames[0] || 'All');
        }
    }, [categoryNames, selectedFoodCategory]);
    const displayedFoodItems = useMemo(() => {
        if (selectedFoodCategory === 'All') return foodItems;
        return foodItemsByCategory[selectedFoodCategory] || [];
    }, [foodItems, foodItemsByCategory, selectedFoodCategory]);

    const goToSignature = useCallback((direction) => {
        setSignatureIndex((prev) => {
            if (!totalSignatureExperiences) return 0;
            return (prev + direction + totalSignatureExperiences) % totalSignatureExperiences;
        });
    }, [totalSignatureExperiences]);

    const getSignatureCardStyle = useCallback((offset) => {
        const abs = Math.abs(offset);
        const horizontalDistance = abs === 1
            ? 'clamp(160px, 24vw, 260px)'
            : 'clamp(260px, 34vw, 380px)';
        const translateX = offset === 0
            ? '0px'
            : offset > 0
                ? horizontalDistance
                : `calc(-1 * ${horizontalDistance})`;
        const translateY = abs === 0
            ? '0px'
            : abs === 1
                ? 'clamp(16px, 4vw, 32px)'
                : 'clamp(28px, 6vw, 52px)';
        const scale = abs === 0 ? 1 : abs === 1 ? 0.9 : 0.78;
        const opacity = abs === 0 ? 1 : abs === 1 ? 0.92 : 0.82;
        const zIndex = abs === 0 ? 50 : abs === 1 ? 40 : 30;
        const boxShadow = abs === 0
            ? '0 25px 45px rgba(12, 61, 38, 0.28)'
            : '0 18px 35px rgba(12, 61, 38, 0.18)';
        const backgroundColor = abs === 0 ? '#ffffff' : 'rgba(255,255,255,0.92)';
        return {
            transform: `translate(-50%, -50%) translate(${translateX}, ${translateY}) scale(${scale})`,
            opacity,
            zIndex,
            boxShadow,
            transition: 'transform 700ms cubic-bezier(.4,0,.2,1), opacity 500ms ease, box-shadow 500ms ease, background-color 500ms ease'
        };
    }, []);

    useEffect(() => {
        if (!totalSignatureExperiences) {
            setSignatureIndex(0);
            return;
        }
        setSignatureIndex(prev => prev % totalSignatureExperiences);
    }, [totalSignatureExperiences]);

    useEffect(() => {
        if (totalSignatureExperiences <= 1) return;
        const timer = setInterval(() => {
            goToSignature(1);
        }, 6000);
        return () => clearInterval(timer);
    }, [totalSignatureExperiences, goToSignature]);

    // Determine gallery card height for a mosaic layout.
    // Specifically, for the SECOND ROW (indices 5-9), apply:
    // [tall, short, tall, tall, short]
    // For other rows, use a gentle alternating pattern for visual rhythm.
    const getGalleryCardHeight = (index) => {
        const columns = 5; // grid is 5 columns on desktop
        const rowIndex = Math.floor(index / columns);
        const colIndex = index % columns;

        // Heights in pixels
        const TALL = 440;
        const SHORT = 280;

        if (rowIndex === 1) {
            const secondRowPattern = [TALL, SHORT, TALL, TALL, SHORT];
            return `${secondRowPattern[colIndex]}px`;
        }

        // Default pattern for other rows (subtle variation)
        const defaultPattern = [320, 360, 300, 360, 320];
        return `${defaultPattern[colIndex]}px`;
    };

    // Fetch all resort data on component mount
    useEffect(() => {
        const fetchResortData = async () => {
            const API_BASE_URL = getApiBaseUrl();

            // Helper: fetch JSON but never throw – log and return fallback on error.
            const safeFetch = async (endpoint, fallback) => {
                try {
                    // Add cache-busting timestamp to force fresh requests
                    const separator = endpoint.includes('?') ? '&' : '?';
                    const cacheBuster = `${separator}_t=${Date.now()}`;
                    const res = await fetch(`${API_BASE_URL}${endpoint}${cacheBuster}`);
                    if (!res.ok) {
                        console.warn(`Endpoint ${endpoint} returned ${res.status}`);
                        return { data: fallback, error: true };
                    }
                    return { data: await res.json(), error: false };
                } catch (e) {
                    console.warn(`Failed to fetch ${endpoint}:`, e);
                    return { data: fallback, error: true };
                }
            };

            try {
                // Essential data for layout
                const roomsResult = await safeFetch("/public/rooms", []);
                const bookingsResult = await safeFetch("/public/bookings?limit=500&skip=0", []);
                const packageBookingsResult = await safeFetch("/public/package-bookings?limit=500&skip=0", []);
                const resortInfoResult = await safeFetch("/resort-info/", []);

                // Non‑critical / image-heavy endpoints – errors should not break the page
                const [
                    foodItemsResult,
                    foodCategoriesResult,
                    packagesResult,
                    galleryResult,
                    reviewsResult,
                    bannerResult,
                    servicesResult,
                    signatureExperiencesResult,
                    planWeddingsResult,
                    nearbyAttractionsResult,
                    nearbyAttractionBannersResult,
                ] = await Promise.all([
                    safeFetch("/public/food-items", []),
                    safeFetch("/public/food-categories", []),
                    safeFetch("/public/packages", []),
                    safeFetch("/gallery/", []),
                    safeFetch("/reviews/", []),
                    safeFetch("/header-banner/", []),
                    safeFetch("/public/services", []),
                    safeFetch("/signature-experiences/", []),
                    safeFetch("/plan-weddings/", []),
                    safeFetch("/nearby-attractions/", []),
                    safeFetch("/nearby-attraction-banners/", []),
                ]);

                const roomsData = roomsResult.data;
                const bookingsData = bookingsResult.data;
                const packageBookingsData = packageBookingsResult.data;
                const resortInfoData = resortInfoResult.data;

                setAllRooms(roomsData);
                // Don't set rooms here - only show after dates are selected
                setBookings(Array.isArray(bookingsData) ? bookingsData : (bookingsData.bookings || []));
                setPackageBookings(packageBookingsData || []);
                setServices(servicesResult.data || []);
                setFoodItems(foodItemsResult.data);
                setFoodCategories(foodCategoriesResult.data || []);
                setPackages(packagesResult.data);
                setResortInfo(resortInfoData.length > 0 ? resortInfoData[0] : null);
                setGalleryImages(galleryResult.data || []);
                setReviews(reviewsResult.data || []);
                setBannerData((bannerResult.data || []).filter((b) => b.is_active));
                setSignatureExperiences(signatureExperiencesResult.data || []);
                setPlanWeddings(planWeddingsResult.data || []);
                setNearbyAttractions(nearbyAttractionsResult.data || []);
                setNearbyAttractionBanners(nearbyAttractionBannersResult.data || []);

                // Only set a global error if the API calls actually failed (not just empty data)
                if (roomsResult.error && resortInfoResult.error) {
                    setError(
                        "Unable to load resort details. Please ensure the backend server is running and accessible."
                    );
                }
            } catch (err) {
                console.error("Unexpected error while fetching resort data:", err);
                setError(
                    "Unexpected error while loading the resort. Please try again later."
                );
            } finally {
                setLoading(false);
            }
        };

        fetchResortData();
    }, []); // run once on mount

    // Auto-rotate banner images - only if multiple banners
    useEffect(() => {
        if (bannerData.length > 1) {
            const interval = setInterval(() => {
                setCurrentBannerIndex((prev) => (prev + 1) % bannerData.length);
            }, 9000); // Slower transition: change image every 9 seconds
            return () => clearInterval(interval);
        } else if (bannerData.length === 1) {
            setCurrentBannerIndex(0); // Ensure first banner is shown
        }
    }, [bannerData.length]);

    // Auto-change wedding images (optimized with pause on hover)
    const [isWeddingHovered, setIsWeddingHovered] = useState(false);
    const activeWeddings = useMemo(() => planWeddings.filter(w => w.is_active), [planWeddings]);
    useEffect(() => {
        if (activeWeddings.length > 1 && !isWeddingHovered) {
            const interval = setInterval(() => {
                setCurrentWeddingIndex((prev) => (prev + 1) % activeWeddings.length);
            }, 10000); // Change image every 10 seconds
            return () => clearInterval(interval);
        } else if (activeWeddings.length === 1) {
            setCurrentWeddingIndex(0); // Ensure first wedding is shown
        }
    }, [activeWeddings.length, isWeddingHovered]);


    useEffect(() => {
        if (totalNearbyAttractionBanners > 1) {
            const interval = setInterval(() => {
                setCurrentAttractionBannerIndex((prev) => (prev + 1) % totalNearbyAttractionBanners);
            }, 9000);
            return () => clearInterval(interval);
        } else if (totalNearbyAttractionBanners === 1) {
            setCurrentAttractionBannerIndex(0);
        }
    }, [totalNearbyAttractionBanners]);

    const toggleChat = () => setIsChatOpen(!isChatOpen);

    // Handlers for opening booking modals
    const handleOpenRoomBookingForm = (roomId) => {
        setBookingData(prev => ({ ...prev, room_ids: prev.room_ids.includes(roomId) ? prev.room_ids : [...prev.room_ids, roomId] }));
        setIsRoomBookingFormOpen(true);
        setBookingMessage({ type: null, text: "" });
    };

    // Lazy reveal on scroll for elements with .reveal - optimized for performance
    useEffect(() => {
        const observer = new IntersectionObserver((entries) => {
            // Use requestAnimationFrame for smoother updates
            requestAnimationFrame(() => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in');
                        observer.unobserve(entry.target);
                    }
                });
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px' // Reduced from 100px for better performance
        });

        const nodes = document.querySelectorAll('.reveal');
        nodes.forEach((n) => observer.observe(n));
        return () => observer.disconnect();
    }, [galleryImages, packages]);

    const handleOpenPackageBookingForm = (packageId) => {
        // Always prioritize dates from bookingData (selected on previous page) over packageBookingData
        setPackageBookingData(prev => {
            const checkIn = (bookingData.check_in && bookingData.check_in.trim() !== '')
                ? bookingData.check_in
                : (prev.check_in && prev.check_in.trim() !== '' ? prev.check_in : '');
            const checkOut = (bookingData.check_out && bookingData.check_out.trim() !== '')
                ? bookingData.check_out
                : (prev.check_out && prev.check_out.trim() !== '' ? prev.check_out : '');

            return {
                ...prev,
                package_id: packageId,
                check_in: checkIn,
                check_out: checkOut
            };
        });
        setIsPackageBookingFormOpen(true);
        setBookingMessage({ type: null, text: "" });
    };

    const handleOpenServiceBookingForm = (serviceId) => {
        setServiceBookingData({ ...serviceBookingData, service_id: serviceId });
        setIsServiceBookingFormOpen(true);
        setBookingMessage({ type: null, text: "" });
    };

    const handleOpenFoodOrderForm = () => {
        setIsFoodOrderFormOpen(true);
        setBookingMessage({ type: null, text: "" });
    };

    // Handlers for form changes
    const handleRoomBookingChange = (e) => {
        const { name, value } = e.target;
        setBookingData(prev => {
            const updated = { ...prev, [name]: value };
            // If check_in is changed and is after check_out, clear check_out
            if (name === 'check_in' && value && prev.check_out && value >= prev.check_out) {
                updated.check_out = '';
            }
            // If check_out is changed and is before check_in, clear check_in
            if (name === 'check_out' && value && prev.check_in && value <= prev.check_in) {
                updated.check_in = '';
            }
            return updated;
        });
    };

    const handleRoomSelection = useCallback((roomId) => {
        setBookingData(prev => {
            const newRoomIds = prev.room_ids.includes(roomId)
                ? prev.room_ids.filter(id => id !== roomId)
                : [...prev.room_ids, roomId];
            return { ...prev, room_ids: newRoomIds };
        });
    }, []);

    const handlePackageBookingChange = (e) => {
        const { name, value } = e.target;
        setPackageBookingData(prev => {
            const updated = { ...prev, [name]: value };
            // If check_in is changed and is after check_out, clear check_out
            if (name === 'check_in' && value && prev.check_out && value >= prev.check_out) {
                updated.check_out = '';
            }
            // If check_out is changed and is before check_in, clear check_in
            if (name === 'check_out' && value && prev.check_in && value <= prev.check_in) {
                updated.check_in = '';
            }
            return updated;
        });
    };

    const handleServiceBookingChange = (e) => {
        const { name, value } = e.target;
        setServiceBookingData(prev => ({ ...prev, [name]: value }));
    };

    const handlePackageRoomSelection = useCallback((roomId) => {
        setPackageBookingData(prev => {
            const newRoomIds = prev.room_ids.includes(roomId)
                ? prev.room_ids.filter(id => id !== roomId)
                : [...prev.room_ids, roomId];
            return { ...prev, room_ids: newRoomIds };
        });
    }, []);

    const handleFoodOrderChange = (e, foodItemId) => {
        const { value } = e.target;
        setFoodOrderData(prev => ({
            ...prev,
            items: {
                ...prev.items,
                [foodItemId]: parseInt(value) || 0,
            }
        }));
    };

    // Check room availability based on selected dates - only show available rooms
    const [roomAvailability, setRoomAvailability] = useState({});

    // Optimized room availability calculation with useMemo and debouncing
    const roomAvailabilityMemo = useMemo(() => {
        if (!bookingData.check_in || !bookingData.check_out || allRooms.length === 0) {
            return {};
        }

        // Calculate availability for each room (memoized for performance)
        const availability = {};
        const requestedCheckIn = new Date(bookingData.check_in);
        const requestedCheckOut = new Date(bookingData.check_out);

        allRooms.forEach(room => {
            // Check conflicts with regular bookings
            const hasRegularConflict = bookings.some(booking => {
                const normalizedStatus = booking.status?.toLowerCase().replace(/_/g, '-');
                // Only check for "booked" or "checked-in" status
                if (normalizedStatus !== "booked" && normalizedStatus !== "checked-in") return false;

                const bookingCheckIn = new Date(booking.check_in);
                const bookingCheckOut = new Date(booking.check_out);

                const isRoomInBooking = booking.rooms && booking.rooms.some(r => {
                    const roomId = r.room?.id || r.id;
                    return roomId === room.id;
                });
                if (!isRoomInBooking) return false;

                return (requestedCheckIn < bookingCheckOut && requestedCheckOut > bookingCheckIn);
            });

            // Check conflicts with package bookings
            const hasPackageConflict = packageBookings.some(packageBooking => {
                const normalizedStatus = packageBooking.status?.toLowerCase().replace(/_/g, '-');
                // Only check for "booked" or "checked-in" status
                if (normalizedStatus !== "booked" && normalizedStatus !== "checked-in") return false;

                const bookingCheckIn = new Date(packageBooking.check_in);
                const bookingCheckOut = new Date(packageBooking.check_out);

                const isRoomInBooking = packageBooking.rooms && packageBooking.rooms.some(r => {
                    // For package bookings, r.id is PackageBookingRoom.id, not room.id
                    // We need to use r.room_id (direct field) or r.room.id (nested object)
                    const roomId = r.room_id || r.room?.id;
                    return roomId === room.id;
                });
                if (!isRoomInBooking) return false;

                return (requestedCheckIn < bookingCheckOut && requestedCheckOut > bookingCheckIn);
            });

            availability[room.id] = !hasRegularConflict && !hasPackageConflict;
        });
        return availability;
    }, [bookingData.check_in, bookingData.check_out, allRooms, bookings, packageBookings]);

    // Update state with debouncing to prevent excessive re-renders
    useEffect(() => {
        const timer = setTimeout(() => {
            setRoomAvailability(roomAvailabilityMemo);
        }, 100); // 100ms debounce
        return () => clearTimeout(timer);
    }, [roomAvailabilityMemo]);

    // Filter rooms to show only available ones when dates are selected
    useEffect(() => {
        if (bookingData.check_in && bookingData.check_out && Object.keys(roomAvailability).length > 0) {
            // Only show available rooms when dates are selected
            const availableRooms = allRooms.filter(room => roomAvailability[room.id] === true);
            setRooms(availableRooms);
        } else {
            // Show all rooms when no dates are selected
            setRooms(allRooms);
        }
    }, [allRooms, bookingData.check_in, bookingData.check_out, roomAvailability]);

    // Package booking availability - optimized with useMemo
    const [packageRoomAvailability, setPackageRoomAvailability] = useState({});

    const packageRoomAvailabilityMemo = useMemo(() => {
        if (!packageBookingData.check_in || !packageBookingData.check_out || allRooms.length === 0 || !isPackageBookingFormOpen || !packageBookingData.package_id) {
            return {};
        }

        // Get the selected package to check booking_type and room_types
        const selectedPackage = packages.find(p => p.id === packageBookingData.package_id);
        if (!selectedPackage) return {};

        // Calculate availability for each room for package booking (memoized for performance)
        const availability = {};
        let roomsToCheck = allRooms;

        // Determine if it's whole_property (same logic as UI)
        const hasRoomTypes = selectedPackage.room_types && selectedPackage.room_types.trim().length > 0;
        const isWholeProperty = selectedPackage.booking_type === 'whole_property' ||
            selectedPackage.booking_type === 'whole property' ||
            (!selectedPackage.booking_type && !hasRoomTypes);

        // Filter by room_types if it's NOT whole_property (i.e., it's room_type)
        // For whole_property, check ALL rooms
        if (!isWholeProperty && selectedPackage.room_types) {
            const allowedRoomTypes = selectedPackage.room_types.split(',').map(t => t.trim().toLowerCase());
            roomsToCheck = allRooms.filter(room => {
                const roomType = room.type ? room.type.trim().toLowerCase() : '';
                return allowedRoomTypes.includes(roomType);
            });
        }
        // For whole_property, roomsToCheck remains allRooms (no filtering)

        // Check availability for each room
        const requestedCheckIn = new Date(packageBookingData.check_in);
        const requestedCheckOut = new Date(packageBookingData.check_out);

        roomsToCheck.forEach(room => {
            // Check conflicts with regular bookings
            const hasRegularConflict = bookings.some(booking => {
                const normalizedStatus = booking.status?.toLowerCase().replace(/_/g, '-');
                // Only check for "booked" or "checked-in" status
                if (normalizedStatus !== "booked" && normalizedStatus !== "checked-in") return false;

                const bookingCheckIn = new Date(booking.check_in);
                const bookingCheckOut = new Date(booking.check_out);

                // Check if this room is part of the booking
                const isRoomInBooking = booking.rooms && booking.rooms.some(r => {
                    // For regular bookings, r.id is the room.id directly
                    const roomId = r.room?.id || r.id;
                    return roomId === room.id;
                });
                if (!isRoomInBooking) return false;

                // Check for date overlap
                return (requestedCheckIn < bookingCheckOut && requestedCheckOut > bookingCheckIn);
            });

            // Check conflicts with package bookings
            const hasPackageConflict = packageBookings.some(packageBooking => {
                const normalizedStatus = packageBooking.status?.toLowerCase().replace(/_/g, '-');
                // Only check for "booked" or "checked-in" status
                if (normalizedStatus !== "booked" && normalizedStatus !== "checked-in") return false;

                const bookingCheckIn = new Date(packageBooking.check_in);
                const bookingCheckOut = new Date(packageBooking.check_out);

                // Check if this room is part of the package booking
                const isRoomInBooking = packageBooking.rooms && packageBooking.rooms.some(r => {
                    // For package bookings, r.id is PackageBookingRoom.id, not room.id
                    // We need to use r.room_id (direct field) or r.room.id (nested object)
                    const roomId = r.room_id || r.room?.id;
                    return roomId === room.id;
                });
                if (!isRoomInBooking) return false;

                // Check for date overlap
                return (requestedCheckIn < bookingCheckOut && requestedCheckOut > bookingCheckIn);
            });

            // Room is available if there are no conflicting bookings (regular or package) for the selected dates
            availability[room.id] = !hasRegularConflict && !hasPackageConflict;
        });

        return availability;
    }, [packageBookingData.check_in, packageBookingData.check_out, packageBookingData.package_id, allRooms, bookings, packageBookings, isPackageBookingFormOpen, packages]);

    // Update state with debouncing to prevent excessive re-renders
    // Also auto-select all available rooms for whole_property packages
    useEffect(() => {
        const timer = setTimeout(() => {
            setPackageRoomAvailability(packageRoomAvailabilityMemo);

            // Auto-select all available rooms for whole_property packages
            if (packageBookingData.package_id && packageBookingData.check_in && packageBookingData.check_out) {
                const selectedPackage = packages.find(p => p.id === packageBookingData.package_id);
                if (selectedPackage) {
                    // Determine if it's whole_property (same logic as UI)
                    const hasRoomTypes = selectedPackage.room_types && selectedPackage.room_types.trim().length > 0;
                    const isWholeProperty = selectedPackage.booking_type === 'whole_property' ||
                        selectedPackage.booking_type === 'whole property' ||
                        (!selectedPackage.booking_type && !hasRoomTypes);

                    if (isWholeProperty) {
                        // Get all available room IDs (rooms that are available for the selected dates)
                        const availableRoomIds = Object.keys(packageRoomAvailabilityMemo)
                            .filter(roomId => packageRoomAvailabilityMemo[roomId] === true)
                            .map(id => parseInt(id));

                        // Always update room_ids for whole_property to ensure all available rooms are selected
                        setPackageBookingData(prev => ({
                            ...prev,
                            room_ids: availableRoomIds
                        }));
                    }
                }
            }
        }, 100); // 100ms debounce
        return () => clearTimeout(timer);
    }, [packageRoomAvailabilityMemo, packageBookingData.package_id, packageBookingData.check_in, packageBookingData.check_out, packages]);

    // Handlers for form submissions
    const handleRoomBookingSubmit = async (e) => {
        e.preventDefault();

        // Prevent multiple submissions
        if (isBookingLoading) {
            return;
        }

        setIsBookingLoading(true);
        setBookingMessage({ type: null, text: "" });

        if (bookingData.room_ids.length === 0) {
            showBannerMessage("error", "Please select at least one room before booking.");
            setIsBookingLoading(false);
            return;
        }

        // --- MINIMUM BOOKING DURATION VALIDATION ---
        if (bookingData.check_in && bookingData.check_out) {
            const checkInDate = new Date(bookingData.check_in);
            const checkOutDate = new Date(bookingData.check_out);
            const timeDiff = checkOutDate.getTime() - checkInDate.getTime();
            const daysDiff = timeDiff / (1000 * 3600 * 24);

            if (daysDiff < 1) {
                showBannerMessage("error", "Minimum 1 day booking is mandatory. Check-out date must be at least 1 day after check-in date.");
                setIsBookingLoading(false);
                return;
            }
        }

        // --- CAPACITY VALIDATION ---
        const selectedRoomDetails = bookingData.room_ids.map(roomId => rooms.find(r => r.id === roomId)).filter(Boolean);
        const roomCapacity = {
            adults: selectedRoomDetails.reduce((sum, room) => sum + (room.adults || 0), 0),
            children: selectedRoomDetails.reduce((sum, room) => sum + (room.children || 0), 0)
        };

        const adultsRequested = parseInt(bookingData.adults);
        const childrenRequested = parseInt(bookingData.children);

        // Validate adults capacity
        if (adultsRequested > roomCapacity.adults) {
            showBannerMessage("error", `The number of adults (${adultsRequested}) exceeds the total adult capacity of the selected rooms (${roomCapacity.adults} adults max). Please select additional rooms or reduce the number of adults.`);
            setIsBookingLoading(false);
            return;
        }

        // Validate children capacity
        if (childrenRequested > roomCapacity.children) {
            showBannerMessage("error", `The number of children (${childrenRequested}) exceeds the total children capacity of the selected rooms (${roomCapacity.children} children max). Please select additional rooms or reduce the number of children.`);
            setIsBookingLoading(false);
            return;
        }
        // -------------------------

        try {
            const API_BASE_URL = getApiBaseUrl();
            const response = await fetch(`${API_BASE_URL}/bookings/guest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(bookingData)
            });

            if (response.ok) {
                showBannerMessage("success", "Room booking successful! We look forward to your stay.");
                setBookingData({ room_ids: [], guest_name: "", guest_mobile: "", guest_email: "", check_in: "", check_out: "", adults: 1, children: 0 });
                // Close the booking form after successful booking
                setTimeout(() => {
                    setIsRoomBookingFormOpen(false);
                }, 2000);
            } else {
                const errorData = await response.json();
                // Check if it's a validation error from the backend
                if (errorData.detail && errorData.detail.includes("Check-out date must be at least 1 day")) {
                    showBannerMessage("error", "Minimum 1 day booking is mandatory. Check-out date must be at least 1 day after check-in date.");
                } else {
                    showBannerMessage("error", `Booking failed: ${errorData.detail || "An unexpected error occurred."}`);
                }
            }
        } catch (err) {
            console.error("Booking API Error:", err);
            showBannerMessage("error", "An error occurred while booking. Please try again.");
        } finally {
            setIsBookingLoading(false);
        }
    };

    const handlePackageBookingSubmit = async (e) => {
        e.preventDefault();

        // Prevent multiple submissions
        if (isBookingLoading) {
            return;
        }

        setIsBookingLoading(true);
        setBookingMessage({ type: null, text: "" });

        // Check if package is whole_property - skip room validation
        const selectedPackage = packages.find(p => p.id === packageBookingData.package_id);
        if (!selectedPackage) {
            showBannerMessage("error", "Package not found. Please select a valid package.");
            setIsBookingLoading(false);
            return;
        }

        // Determine if it's whole_property (same logic as UI)
        const hasRoomTypes = selectedPackage.room_types && selectedPackage.room_types.trim().length > 0;
        const isWholeProperty = selectedPackage.booking_type === 'whole_property' ||
            selectedPackage.booking_type === 'whole property' ||
            (!selectedPackage.booking_type && !hasRoomTypes);

        // For whole_property, get all available rooms and use them directly
        let finalRoomIds = packageBookingData.room_ids;

        if (isWholeProperty) {
            // For whole_property, get ALL available rooms from the system
            // Check availability for all rooms based on selected dates
            const availableRoomIds = allRooms
                .filter(room => {
                    // Check if room has any conflicting bookings
                    const hasConflict = bookings.some(booking => {
                        const normalizedStatus = booking.status?.toLowerCase().replace(/_/g, '-');
                        // Only check for "booked" or "checked-in" status
                        if (normalizedStatus !== "booked" && normalizedStatus !== "checked-in") return false;

                        const bookingCheckIn = new Date(booking.check_in);
                        const bookingCheckOut = new Date(booking.check_out);
                        const requestedCheckIn = new Date(packageBookingData.check_in);
                        const requestedCheckOut = new Date(packageBookingData.check_out);

                        // Check if this room is part of the booking
                        const isRoomInBooking = booking.rooms && booking.rooms.some(r => {
                            const roomId = r.room?.id || r.id;
                            return roomId === room.id;
                        });
                        if (!isRoomInBooking) return false;

                        // Check for date overlap
                        return (requestedCheckIn < bookingCheckOut && requestedCheckOut > bookingCheckIn);
                    });

                    return !hasConflict; // Room is available if no conflicts
                })
                .map(room => room.id);

            if (availableRoomIds.length === 0) {
                showBannerMessage("error", "No rooms are available for the selected dates.");
                setIsBookingLoading(false);
                return;
            }

            // Use all available rooms for whole_property
            finalRoomIds = availableRoomIds;
        } else {
            // For room_type packages, validate that at least one room is selected
            if (packageBookingData.room_ids.length === 0) {
                showBannerMessage("error", "Please select at least one room for the package.");
                setIsBookingLoading(false);
                return;
            }
            finalRoomIds = packageBookingData.room_ids;
        }

        // --- MINIMUM BOOKING DURATION VALIDATION ---
        if (packageBookingData.check_in && packageBookingData.check_out) {
            const checkInDate = new Date(packageBookingData.check_in);
            const checkOutDate = new Date(packageBookingData.check_out);
            const timeDiff = checkOutDate.getTime() - checkInDate.getTime();
            const daysDiff = timeDiff / (1000 * 3600 * 24);

            if (daysDiff < 1) {
                showBannerMessage("error", "Minimum 1 day booking is mandatory. Check-out date must be at least 1 day after check-in date.");
                setIsBookingLoading(false);
                return;
            }
        }

        // --- CAPACITY VALIDATION ---
        // Skip capacity validation for whole_property packages (they book entire property regardless of guest count)
        if (!isWholeProperty) {
            const selectedRoomDetails = finalRoomIds.map(roomId => rooms.find(r => r.id === roomId)).filter(Boolean);
            const packageCapacity = {
                adults: selectedRoomDetails.reduce((sum, room) => sum + (room.adults || 0), 0),
                children: selectedRoomDetails.reduce((sum, room) => sum + (room.children || 0), 0)
            };

            const adultsRequested = parseInt(packageBookingData.adults);
            const childrenRequested = parseInt(packageBookingData.children);

            // Validate adults capacity
            if (adultsRequested > packageCapacity.adults) {
                showBannerMessage("error", `The number of adults (${adultsRequested}) exceeds the total adult capacity of the selected rooms (${packageCapacity.adults} adults max). Please select additional rooms or reduce the number of adults.`);
                setIsBookingLoading(false);
                return;
            }

            // Validate children capacity
            if (childrenRequested > packageCapacity.children) {
                showBannerMessage("error", `The number of children (${childrenRequested}) exceeds the total children capacity of the selected rooms (${packageCapacity.children} children max). Please select additional rooms or reduce the number of children.`);
                setIsBookingLoading(false);
                return;
            }
        }
        // -------------------------

        try {
            const API_BASE_URL = getApiBaseUrl();

            // Validate required fields
            if (!packageBookingData.package_id) {
                showBannerMessage("error", "Package ID is missing. Please select a package.");
                setIsBookingLoading(false);
                return;
            }

            if (!packageBookingData.check_in || !packageBookingData.check_out) {
                showBannerMessage("error", "Please select check-in and check-out dates.");
                setIsBookingLoading(false);
                return;
            }

            if (!packageBookingData.guest_name) {
                showBannerMessage("error", "Please enter your full name.");
                setIsBookingLoading(false);
                return;
            }

            // Email and mobile are optional in the schema, but we'll recommend at least one
            if (!packageBookingData.guest_email && !packageBookingData.guest_mobile) {
                showBannerMessage("error", "Please provide at least an email address or mobile number.");
                setIsBookingLoading(false);
                return;
            }

            const payload = {
                package_id: parseInt(packageBookingData.package_id),
                room_ids: finalRoomIds.map(id => parseInt(id)), // Use finalRoomIds (all available for whole_property, selected for room_type)
                guest_name: packageBookingData.guest_name.trim(),
                guest_email: packageBookingData.guest_email?.trim() || null,
                guest_mobile: packageBookingData.guest_mobile.trim(),
                check_in: packageBookingData.check_in,
                check_out: packageBookingData.check_out,
                adults: parseInt(packageBookingData.adults) || 1,
                children: parseInt(packageBookingData.children) || 0,
                food_preferences: packageBookingData.food_preferences,
                special_requests: packageBookingData.special_requests
            };

            console.log("Package Booking Payload:", payload); // Debug log

            const response = await fetch(`${API_BASE_URL}/packages/book/guest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showBannerMessage("success", "Package booking successful! We look forward to your stay.");
                setPackageBookingData({ package_id: null, room_ids: [], guest_name: "", guest_mobile: "", guest_email: "", check_in: "", check_out: "", adults: 1, children: 0 });
                // Close the booking form after successful booking
                setTimeout(() => {
                    setIsPackageBookingFormOpen(false);
                }, 2000);
            } else {
                let errorMessage = "An unexpected error occurred.";
                try {
                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.includes("application/json")) {
                        const errorData = await response.json();
                        console.error("Package Booking Error Response:", errorData);

                        // Check if it's a validation error from the backend
                        if (errorData.detail) {
                            if (typeof errorData.detail === 'string') {
                                errorMessage = errorData.detail;
                            } else if (Array.isArray(errorData.detail)) {
                                // Handle Pydantic validation errors
                                const errors = errorData.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
                                errorMessage = `Validation error: ${errors}`;
                            } else {
                                errorMessage = JSON.stringify(errorData.detail);
                            }
                        }
                    } else {
                        const textError = await response.text();
                        console.error("Error response text:", textError);
                        errorMessage = textError || `Server error (${response.status}): ${response.statusText}`;
                    }
                } catch (parseError) {
                    console.error("Failed to parse error response:", parseError);
                    errorMessage = `Server error (${response.status}): ${response.statusText}`;
                }
                showBannerMessage("error", `Package booking failed: ${errorMessage}`);
            }
        } catch (err) {
            console.error("Package Booking API Error:", err);
            showBannerMessage("error", `An error occurred while booking the package: ${err.message || "Please check your connection and try again."}`);
        } finally {
            setIsBookingLoading(false);
        }
    };

    const handleServiceBookingSubmit = async (e) => {
        e.preventDefault();
        setIsBookingLoading(true);
        setBookingMessage({ type: null, text: "" });

        try {
            const API_BASE_URL = getApiBaseUrl();
            const response = await fetch(`${API_BASE_URL}/services/bookings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(serviceBookingData)
            });

            if (response.ok) {
                showBannerMessage("success", "Service booking successful! Our staff will be with you shortly.");
                setServiceBookingData({ service_id: null, guest_name: "", guest_mobile: "", guest_email: "", room_id: null });
                // Close the booking form after successful booking
                setTimeout(() => {
                    setIsServiceBookingFormOpen(false);
                }, 2000);
            } else {
                const errorData = await response.json();
                showBannerMessage("error", `Service booking failed: ${errorData.detail || "An unexpected error occurred."}`);
            }
        } catch (err) {
            console.error("Service Booking API Error:", err);
            showBannerMessage("error", "An error occurred while booking the service. Please try again.");
        } finally {
            setIsBookingLoading(false);
        }
    };

    const handleFoodOrderSubmit = async (e) => {
        e.preventDefault();
        setIsBookingLoading(true);
        setBookingMessage({ type: null, text: "" });

        const itemsPayload = Object.entries(foodOrderData.items)
            .filter(([, quantity]) => quantity > 0)
            .map(([food_item_id, quantity]) => ({ food_item_id: parseInt(food_item_id), quantity }));

        if (itemsPayload.length === 0) {
            showBannerMessage("error", "Please select at least one food item.");
            setIsBookingLoading(false);
            return;
        }

        const payload = {
            room_id: foodOrderData.room_id,
            items: itemsPayload,
            amount: 0, // Amount will be calculated by the backend
            assigned_employee_id: 0,
            billing_status: "unbilled"
        };

        try {
            const API_BASE_URL = getApiBaseUrl();
            const response = await fetch(`${API_BASE_URL}/food-orders/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showBannerMessage("success", "Food order placed successfully! Your meal will be delivered shortly.");
                setFoodOrderData({ room_id: null, items: {} });
                // Close the booking form after successful order
                setTimeout(() => {
                    setIsFoodOrderFormOpen(false);
                }, 2000);
            } else {
                const errorData = await response.json();
                showBannerMessage("error", `Food order failed: ${errorData.detail || "An unexpected error occurred."}`);
            }
        } catch (err) {
            console.error("Food Order API Error:", err);
            showBannerMessage("error", "An error occurred while placing the food order. Please try again.");
        } finally {
            setIsBookingLoading(false);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!userMessage.trim() || isChatLoading) return;

        const newUserMessage = { role: "user", parts: [{ text: userMessage }] };
        setChatHistory(prev => [...prev, newUserMessage]);
        setUserMessage("");
        setIsChatLoading(true);

        try {
            // Replace with your actual Gemini API key
            const apiKey = "YOUR_GEMINI_API_KEY";
            if (apiKey === "YOUR_GEMINI_API_KEY") {
                setChatHistory(prev => [...prev, { role: "model", parts: [{ text: "Please replace 'YOUR_GEMINI_API_KEY' with your actual API key in App.js." }] }]);
                setIsChatLoading(false);
                return;
            }

            const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${apiKey}`;
            const payload = { contents: [...chatHistory, newUserMessage] };

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error(`API call failed: ${response.status}`);

            const result = await response.json();
            const botResponse = result.candidates?.[0]?.content?.parts?.[0]?.text;

            if (botResponse) {
                setChatHistory(prev => [...prev, { role: "model", parts: [{ text: botResponse }] }]);
            } else {
                setChatHistory(prev => [...prev, { role: "model", parts: [{ text: "I'm sorry, I couldn't generate a response." }] }]);
            }
        } catch (err) {
            console.error("Gemini API Error:", err);
            setChatHistory(prev => [...prev, { role: "model", parts: [{ text: "I'm having trouble connecting. Please check your API key and network." }] }]);
        } finally {
            setIsChatLoading(false);
        }
    };

    useEffect(() => {
        if (chatMessagesRef.current) {
            chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
        }
    }, [chatHistory]);

    useEffect(() => {
        // Apply theme to document body for better visibility
        document.documentElement.className = '';
        document.body.className = `${theme.bgPrimary} ${theme.textPrimary} transition-colors duration-500`;
    }, [theme]);


    // Debounced scroll handler for better performance
    useEffect(() => {
        let ticking = false;
        const handleScroll = () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    setShowBackToTop(window.scrollY > 300);
                    ticking = false;
                });
                ticking = true;
            }
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToTop = () => window.scrollTo({ top: 0, behavior: 'smooth' });

    const sectionTitleStyle = `text-3xl md:text-5xl font-extrabold mb-8 text-center tracking-tight bg-gradient-to-r ${theme.textTitleGradient} text-transparent bg-clip-text`;
    const cardStyle = `flex-none w-80 md:w-96 ${theme.bgCard} rounded-3xl overflow-hidden shadow-2xl transition-all duration-500 ease-in-out border ${theme.border} ${theme.borderHover} transform group-hover:-translate-y-1 group-hover:shadow-lg`;
    const iconStyle = `w-6 h-6 ${theme.textAccent} transition-transform duration-300 group-hover:rotate-12`;
    const textPrimary = theme.textPrimary;
    const textSecondary = theme.textSecondary;
    const priceStyle = `font-bold text-xl ${theme.textAccent} tracking-wider`;
    const buttonStyle = `mt-4 inline-flex items-center text-sm font-semibold ${theme.textAccent} hover:text-white transition duration-300`;

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-transparent">
                <div className="flex flex-col items-center space-y-6">
                    <div className="relative">
                        <div className="w-28 h-28 md:w-32 md:h-32 rounded-full border-4 border-amber-400/30 border-t-amber-500 animate-spin shadow-lg" />
                        <div className="absolute inset-3 md:inset-4 rounded-full bg-amber-500 flex items-center justify-center shadow-2xl border-2 border-amber-300/20">
                            <img
                                src={logoSrc || localLogo}
                                alt="Resort"
                                className="h-16 w-auto md:h-20 object-contain"
                            />
                        </div>
                    </div>
                    <div className="text-center">
                        <p className="text-xs md:text-sm tracking-[0.25em] uppercase text-amber-600 font-bold">
                            Resort
                        </p>
                        <p className="mt-2 text-xs md:text-sm text-gray-700">
                            Crafting your perfect stay...
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className={`flex items-center justify-center min-h-screen ${theme.bgPrimary} text-red-400`}>
                <p className={`p-4 ${theme.bgCard} rounded-lg shadow-lg`}>{error}</p>
            </div>
        );
    }

    return (
        <>
            <style>{`
              @keyframes auto-scroll-bobbing { 0% { transform: translate(0, 0); } 25% { transform: translate(-12.5%, 3px); } 50% { transform: translate(-25%, 0); } 75% { transform: translate(-37.5%, -3px); } 100% { transform: translate(-50%, 0); } }
              @keyframes auto-scroll-bobbing-reverse { 0% { transform: translate(-50%, 0); } 25% { transform: translate(-37.5%, 3px); } 50% { transform: translate(-25%, 0); } 75% { transform: translate(-12.5%, -3px); } 100% { transform: translate(0, 0); } }
              @keyframes auto-scroll-reverse { from { transform: translateX(-50%); } to { transform: translateX(0); } }
              @keyframes auto-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
              .horizontal-scroll-container { -ms-overflow-style: none; scrollbar-width: none; }
              .horizontal-scroll-container::-webkit-scrollbar { display: none; }
              @keyframes bounce-dot { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }
              .animate-bounce-dot > div { animation: bounce-dot 1.4s infinite ease-in-out both; }
            `}</style>

            <div className={`relative ${theme.bgPrimary} ${theme.textPrimary} font-sans min-h-screen transition-colors duration-500`}>
                <BackgroundAnimation theme={theme} />

                {/* Banner Message - High z-index to appear above all modals and overlays */}
                {bannerMessage.text && (
                    <div
                        className={`fixed top-0 left-0 right-0 z-[99999] p-4 text-white text-center font-medium shadow-2xl transform transition-all duration-300 ${bannerMessage.type === 'success' ? 'bg-green-600' :
                            bannerMessage.type === 'error' ? 'bg-red-600' :
                                bannerMessage.type === 'warning' ? 'bg-yellow-600' :
                                    'bg-blue-600'
                            }`}
                        style={{
                            zIndex: 99999,
                            pointerEvents: 'auto'
                        }}
                    >
                        <div className="flex items-center justify-center relative max-w-7xl mx-auto">
                            <span className="mr-2">
                                {bannerMessage.type === 'success' ? '✅' :
                                    bannerMessage.type === 'error' ? '❌' :
                                        bannerMessage.type === 'warning' ? '⚠️' :
                                            'ℹ️'}
                            </span>
                            <span className="flex-1">{bannerMessage.text}</span>
                            <button
                                onClick={() => setBannerMessage({ type: null, text: "" })}
                                className="ml-4 p-1 rounded-full hover:bg-white/20 transition-colors"
                                aria-label="Close message"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                )}

                <header className={`fixed left-0 right-0 z-50 h-20 md:h-24 ${bannerMessage.text ? 'top-16' : 'top-0'} transition-all duration-300`}>
                    {/* Blur Background */}
                    <div className="absolute inset-0 bg-white/80 dark:bg-black/80 backdrop-blur-md border-b border-white/20 dark:border-white/10"></div>

                    <div className="container mx-auto px-4 sm:px-6 md:px-12 h-full flex items-center justify-between relative z-10">
                        {/* Logo */}
                        <div className="flex items-center space-x-3 h-full">
                            <div className="p-3 md:p-4 rounded-xl flex items-center justify-center shadow-lg border-2 bg-gradient-to-br from-gray-800 via-gray-900 to-black" style={{ borderColor: 'rgba(212, 175, 55, 0.3)' }}>
                                <img
                                    src={logoSrc}
                                    alt="Resort logo"
                                    className="h-10 md:h-12 w-auto object-contain drop-shadow-md"
                                    loading="lazy"
                                    onError={() => {
                                        setLogoIndex((prev) => {
                                            const next = prev + 1;
                                            return next < logoCandidates.length ? next : prev;
                                        });
                                    }}
                                />
                            </div>
                        </div>

                        {/* Desktop Navigation Menu */}
                        <nav className="hidden lg:flex items-center space-x-1">
                            <a
                                href="#packages"
                                onClick={(e) => {
                                    e.preventDefault();
                                    document.getElementById('packages')?.scrollIntoView({ behavior: 'smooth' });
                                    setIsMobileMenuOpen(false);
                                }}
                                className="px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors duration-200 rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                            >
                                Exclusive Deals
                            </a>
                            <a
                                href="#rooms-section"
                                onClick={(e) => {
                                    e.preventDefault();
                                    document.getElementById('rooms-section')?.scrollIntoView({ behavior: 'smooth' });
                                    setIsMobileMenuOpen(false);
                                }}
                                className="px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors duration-200 rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                            >
                                Rooms
                            </a>
                            <a
                                href="#services"
                                onClick={(e) => {
                                    e.preventDefault();
                                    const servicesSection = document.querySelector('[data-services-section]');
                                    if (servicesSection) {
                                        servicesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    }
                                    setIsMobileMenuOpen(false);
                                }}
                                className="px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors duration-200 rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                            >
                                Services
                            </a>
                            <a
                                href="#food"
                                onClick={(e) => {
                                    e.preventDefault();
                                    const foodSection = document.querySelector('[data-food-section]');
                                    if (foodSection) {
                                        foodSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    }
                                    setIsMobileMenuOpen(false);
                                }}
                                className="px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors duration-200 rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                            >
                                Food
                            </a>
                            <a
                                href="#gallery"
                                onClick={(e) => {
                                    e.preventDefault();
                                    const gallerySection = document.querySelector('[data-gallery-section]');
                                    if (gallerySection) {
                                        gallerySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    }
                                    setIsMobileMenuOpen(false);
                                }}
                                className="px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors duration-200 rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                            >
                                Gallery
                            </a>
                            <a
                                href="#reviews"
                                onClick={(e) => {
                                    e.preventDefault();
                                    const reviewsSection = document.querySelector('[data-reviews-section]');
                                    if (reviewsSection) {
                                        reviewsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    }
                                    setIsMobileMenuOpen(false);
                                }}
                                className="px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors duration-200 rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                            >
                                Reviews
                            </a>
                            <a
                                href="#contact"
                                onClick={(e) => {
                                    e.preventDefault();
                                    const contactSection = document.querySelector('[data-contact-section]');
                                    if (contactSection) {
                                        contactSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                    }
                                    setIsMobileMenuOpen(false);
                                }}
                                className="px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors duration-200 rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                            >
                                Contact
                            </a>
                        </nav>

                        {/* Book Now Button & Mobile Menu Toggle */}
                        <div className="flex items-center space-x-3">
                            <button
                                onClick={() => { setShowAmenities(false); setIsGeneralBookingOpen(true); }}
                                className="hidden sm:block px-6 md:px-8 py-2.5 md:py-3.5 text-xs md:text-sm font-bold text-[#1a472a] bg-gradient-to-r from-[#d4af37] via-[#f4d03f] to-[#d4af37] rounded-lg shadow-xl hover:shadow-2xl hover:from-[#f4d03f] hover:via-[#ffd700] hover:to-[#f4d03f] transition-all duration-300 transform hover:scale-105 border-2 border-[#b8941f] uppercase tracking-wider focus:outline-none focus:ring-4 focus:ring-[#d4af37]/50"
                            >
                                Book Now
                            </button>

                            {/* Mobile Menu Toggle */}
                            <button
                                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                                className="lg:hidden p-2 text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 transition-colors rounded-lg hover:bg-white/50 dark:hover:bg-white/10"
                                aria-label="Toggle menu"
                            >
                                {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                            </button>
                        </div>
                    </div>

                    {/* Mobile Navigation Menu */}
                    {isMobileMenuOpen && (
                        <div className="lg:hidden absolute top-full left-0 right-0 bg-white/95 dark:bg-black/95 backdrop-blur-md border-b border-white/20 dark:border-white/10 shadow-xl">
                            <nav className="container mx-auto px-4 py-4 space-y-2">
                                <a
                                    href="#packages"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        document.getElementById('packages')?.scrollIntoView({ behavior: 'smooth' });
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="block px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 hover:bg-white/50 dark:hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Exclusive Deals
                                </a>
                                <a
                                    href="#rooms-section"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        document.getElementById('rooms-section')?.scrollIntoView({ behavior: 'smooth' });
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="block px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 hover:bg-white/50 dark:hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Rooms
                                </a>
                                <a
                                    href="#services"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        const servicesSection = document.querySelector('[data-services-section]');
                                        if (servicesSection) {
                                            servicesSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="block px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 hover:bg-white/50 dark:hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Services
                                </a>
                                <a
                                    href="#food"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        const foodSection = document.querySelector('[data-food-section]');
                                        if (foodSection) {
                                            foodSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="block px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 hover:bg-white/50 dark:hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Food
                                </a>
                                <a
                                    href="#gallery"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        const gallerySection = document.querySelector('[data-gallery-section]');
                                        if (gallerySection) {
                                            gallerySection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="block px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 hover:bg-white/50 dark:hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Gallery
                                </a>
                                <a
                                    href="#reviews"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        const reviewsSection = document.querySelector('[data-reviews-section]');
                                        if (reviewsSection) {
                                            reviewsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="block px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 hover:bg-white/50 dark:hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Reviews
                                </a>
                                <a
                                    href="#contact"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        const contactSection = document.querySelector('[data-contact-section]');
                                        if (contactSection) {
                                            contactSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        }
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="block px-4 py-3 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-[#0f5132] dark:hover:text-amber-400 hover:bg-white/50 dark:hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    Contact
                                </a>
                                <button
                                    onClick={() => {
                                        setShowAmenities(false);
                                        setIsGeneralBookingOpen(true);
                                        setIsMobileMenuOpen(false);
                                    }}
                                    className="w-full mt-4 px-6 py-3 text-sm font-bold text-[#1a472a] bg-gradient-to-r from-[#d4af37] via-[#f4d03f] to-[#d4af37] rounded-lg shadow-xl hover:shadow-2xl hover:from-[#f4d03f] hover:via-[#ffd700] hover:to-[#f4d03f] transition-all duration-300 transform hover:scale-105 border-2 border-[#b8941f] uppercase tracking-wider"
                                >
                                    Book Now
                                </button>
                            </nav>
                        </div>
                    )}
                </header>

                <main className="w-full max-w-full pt-0 space-y-0 relative z-10 overflow-hidden">
                    {/* Hero Banner Section - Image Only */}
                    <div
                        ref={bannerRef}
                        className="relative w-full h-screen overflow-hidden bg-white"
                    >
                        {bannerData.length > 0 ? (
                            <>
                                {/* Banner Images Background */}
                                {bannerData.map((banner, index) => (
                                    <img
                                        key={banner.id}
                                        src={getImageUrl(banner.image_url)}
                                        onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                        alt={banner.title}
                                        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ${index === currentBannerIndex ? 'opacity-100 animate-zoom-gentle' : 'opacity-0'}`}
                                    />
                                ))}
                            </>
                        ) : (
                            <div className="absolute inset-0 bg-gray-100"></div>
                        )}

                        {/* Hero Content */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6 z-10">
                            <div className="max-w-5xl mx-auto">
                                {/* Contact Info */}
                                {resortInfo && (
                                    <div className="flex flex-wrap items-center justify-center gap-6 md:gap-8 mb-10 text-white text-sm md:text-base drop-shadow-lg animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                                        {resortInfo.email && (
                                            <span className="flex items-center gap-2 px-4 py-2 bg-black/50 backdrop-blur-sm rounded-lg border border-white/20 shadow-md animate-float-gentle" style={{ animationDelay: '0.3s' }}>
                                                <span className="text-white">✉</span>
                                                {resortInfo.email}
                                            </span>
                                        )}
                                        {resortInfo.phone && (
                                            <span className="flex items-center gap-2 px-4 py-2 bg-black/50 backdrop-blur-sm rounded-lg border border-white/20 shadow-md animate-float-gentle" style={{ animationDelay: '0.4s' }}>
                                                <span className="text-white">📞</span>
                                                {resortInfo.phone}
                                            </span>
                                        )}
                                    </div>
                                )}

                                {/* Main Heading - Banner Title and Description */}
                                {bannerData.length > 0 && bannerData[currentBannerIndex] && (
                                    <div className="mb-10 animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
                                        {bannerData[currentBannerIndex].title && (
                                            <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold mb-4 leading-tight text-white drop-shadow-2xl animate-slide-in-left">
                                                {bannerData[currentBannerIndex].title}
                                            </h1>
                                        )}
                                        {bannerData[currentBannerIndex].subtitle && (
                                            <p className="text-3xl md:text-4xl lg:text-5xl font-medium leading-relaxed text-white/90 drop-shadow-lg animate-slide-in-right">
                                                {bannerData[currentBannerIndex].subtitle}
                                            </p>
                                        )}
                                    </div>
                                )}
                                {(!bannerData.length || !bannerData[currentBannerIndex]) && (
                                    <h1 className="text-4xl md:text-6xl lg:text-8xl font-extrabold mb-10 leading-tight text-white drop-shadow-2xl animate-fade-in-up">
                                        Stay enjoying the cozy indoors
                                        <br />
                                        and tranquil outdoors.
                                    </h1>
                                )}
                            </div>

                            {/* Book Now Button at Bottom */}
                            <div className="absolute bottom-20 left-1/2 -translate-x-1/2 animate-bounce-gentle">
                                <button
                                    type="button"
                                    onClick={() => { setShowAmenities(false); setIsGeneralBookingOpen(true); }}
                                    className="px-12 py-5 bg-black/80 text-white font-bold text-lg md:text-xl rounded-xl shadow-2xl hover:bg-black/90 transition-all duration-300 transform hover:scale-105 border-2 border-white/30 uppercase tracking-wider backdrop-blur-sm animate-pulse-gentle"
                                >
                                    Book Now
                                </button>
                            </div>
                        </div>

                        {/* Navigation Dots - Only show if multiple banners */}
                        {bannerData.length > 1 && (
                            <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex space-x-3 z-20">
                                {bannerData.map((_, index) => (
                                    <button
                                        key={index}
                                        onClick={() => setCurrentBannerIndex(index)}
                                        className={`transition-all duration-300 ${index === currentBannerIndex
                                            ? "w-12 h-1 bg-white rounded-full"
                                            : "w-8 h-1 bg-white/40 hover:bg-white/70 rounded-full"
                                            }`}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Exclusive Deals Section - Resort Style */}
                    <section id="packages" className="bg-gradient-to-b from-[#f4ede1] via-[#f9f4ea] to-white py-20 transition-colors duration-500">
                        <div className="w-full mx-auto px-2 sm:px-4 md:px-6">
                            {/* Section Header */}
                            <div className="text-center mb-16">
                                <span className="inline-block px-6 py-2 bg-[#0f5132]/10 text-[#0f5132] text-sm font-semibold tracking-[0.35em] uppercase rounded-full border border-[#d8c9ac] mb-4">
                                    ✦ Exclusive Deals ✦
                                </span>
                                <h2 className="text-4xl md:text-5xl font-extrabold text-[#153a2c] mb-4">
                                    EXCLUSIVE DEALS FOR MEMORABLE EXPERIENCES
                                </h2>
                            </div>

                            {/* Packages - Mountain Shadows Style */}
                            {packages.length > 0 ? (
                                <div className="space-y-12">
                                    {/* Featured Large Package */}
                                    {packages[0] && (() => {
                                        const featuredPkg = packages[0];
                                        const imgIndex = packageImageIndex[featuredPkg.id] || 0;
                                        const currentImage = featuredPkg.images && featuredPkg.images[imgIndex];
                                        return (
                                            <div
                                                key={featuredPkg.id}
                                                className={`${theme.bgCard} rounded-3xl overflow-hidden shadow-2xl border ${theme.border} transition-all duration-500 hover:shadow-3xl reveal`}
                                                style={{ transitionDelay: '80ms' }}
                                            >
                                                <div className="flex flex-col md:flex-row items-stretch">
                                                    {/* Large Image Section - Left */}
                                                    <div className="w-full md:w-1/2 h-80 md:h-[500px] overflow-hidden relative">
                                                        <img
                                                            src={currentImage ? getImageUrl(currentImage.image_url) : ITEM_PLACEHOLDER}
                                                            alt={featuredPkg.title}
                                                            className="w-full h-full object-cover transition-transform duration-700 hover:scale-110 reveal"
                                                            loading="lazy"
                                                            onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                        />
                                                        {/* Price badge - large card */}
                                                        <div className="absolute bottom-4 left-4 bg-[#0f5132]/90 text-white font-extrabold text-2xl md:text-3xl px-4 py-2 rounded-xl shadow-lg border border-white/20 backdrop-blur-sm">
                                                            {formatCurrency(featuredPkg.price || 0)}
                                                        </div>
                                                        {/* Image Slider Dots */}
                                                        {featuredPkg.images && featuredPkg.images.length > 1 && (
                                                            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-black/60 backdrop-blur-sm px-3 py-2 rounded-full z-10">
                                                                {featuredPkg.images.map((_, imgIdx) => (
                                                                    <button
                                                                        key={imgIdx}
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            setPackageImageIndex(prev => ({ ...prev, [featuredPkg.id]: imgIdx }));
                                                                        }}
                                                                        className={`w-2 h-2 rounded-full transition-all ${imgIdx === imgIndex ? 'bg-white' : 'bg-white/40'}`}
                                                                    />
                                                                ))}
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Content Section - Right */}
                                                    <div className={`w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center ${theme.bgCard}`}>
                                                        <h3 className={`text-4xl md:text-5xl font-extrabold ${theme.textPrimary} mb-2 leading-tight`}>
                                                            {featuredPkg.title}
                                                        </h3>
                                                        {featuredPkg.duration && (
                                                            <p className={`text-xl md:text-2xl ${theme.textSecondary} mb-6 font-medium`}>
                                                                {featuredPkg.duration}
                                                            </p>
                                                        )}
                                                        <div className="w-20 h-1 bg-gradient-to-r from-[#0f5132] via-[#1a7042] to-[#c99c4e] mb-6"></div>
                                                        <p className={`text-base md:text-lg ${theme.textSecondary} leading-relaxed mb-6`}>
                                                            {featuredPkg.description}
                                                        </p>
                                                        {/* Price Section */}
                                                        <div className="mb-6 pt-4 border-t border-gray-200">
                                                            <p className={`text-sm ${theme.textSecondary} mb-2`}>Starting from</p>
                                                            <p className={`text-3xl md:text-4xl font-extrabold ${theme.textAccent} mb-6`}>
                                                                {formatCurrency(featuredPkg.price || 0)}
                                                                <span className={`text-lg ${theme.textSecondary} font-normal ml-2`}>/package</span>
                                                            </p>
                                                        </div>

                                                        <div className="flex items-center justify-between flex-wrap gap-4">
                                                            <button
                                                                onClick={() => handleOpenPackageBookingForm(featuredPkg.id)}
                                                                className="px-8 py-3 bg-gradient-to-r from-[#d4af37] via-[#f4d03f] to-[#d4af37] text-[#1a472a] font-bold rounded-lg shadow-xl hover:shadow-2xl hover:from-[#f4d03f] hover:via-[#ffd700] hover:to-[#f4d03f] transition-all duration-300 transform hover:scale-105 flex items-center gap-2 border-2 border-[#b8941f] uppercase tracking-wider focus:outline-none focus:ring-4 focus:ring-[#d4af37]/50"
                                                            >
                                                                Book Now
                                                                <ChevronRight className="w-5 h-5" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })()}

                                    {/* Smaller Packages Grid - Only show if more than 1 package */}
                                    {packages.length > 1 && (
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                            {packages.slice(1).map((pkg) => {
                                                const imgIndex = packageImageIndex[pkg.id] || 0;
                                                const currentImage = pkg.images && pkg.images[imgIndex];
                                                return (
                                                    <div
                                                        key={pkg.id}
                                                        onClick={() => handleOpenPackageBookingForm(pkg.id)}
                                                        className={`group relative ${theme.bgCard} rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-500 border ${theme.border} cursor-pointer reveal`}
                                                        style={{ transitionDelay: `${(imgIndex % 5) * 70}ms` }}
                                                    >
                                                        {/* Image Container */}
                                                        <div className="relative h-64 overflow-hidden">
                                                            <img
                                                                src={currentImage ? getImageUrl(currentImage.image_url) : ITEM_PLACEHOLDER}
                                                                alt={pkg.title}
                                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 reveal"
                                                                loading="lazy"
                                                                onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                            />
                                                            {/* Price badge - always visible */}
                                                            <div className="absolute bottom-3 left-3 bg-gradient-to-r from-[#d4af37]/95 to-[#f4d03f]/95 text-[#1a472a] font-extrabold text-lg px-3 py-1 rounded-lg shadow-xl border-2 border-[#b8941f]/50 backdrop-blur-sm">
                                                                {formatCurrency(pkg.price || 0)}
                                                            </div>
                                                            {/* Quick Book button overlay */}
                                                            <button
                                                                type="button"
                                                                onClick={(e) => { e.stopPropagation(); handleOpenPackageBookingForm(pkg.id); }}
                                                                className="absolute top-3 right-3 bg-gradient-to-r from-[#d4af37] via-[#f4d03f] to-[#d4af37] text-[#1a472a] text-xs font-bold px-3 py-1 rounded-lg shadow-lg hover:shadow-xl hover:from-[#f4d03f] hover:via-[#ffd700] hover:to-[#f4d03f] border border-[#b8941f] uppercase tracking-wide transition-all duration-300"
                                                            >
                                                                Book Now
                                                            </button>
                                                            {/* Image Slider Dots */}
                                                            {pkg.images && pkg.images.length > 1 && (
                                                                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-black/60 backdrop-blur-sm px-3 py-2 rounded-full z-10">
                                                                    {pkg.images.map((_, imgIdx) => (
                                                                        <button
                                                                            key={imgIdx}
                                                                            onClick={(e) => {
                                                                                e.stopPropagation();
                                                                                setPackageImageIndex(prev => ({ ...prev, [pkg.id]: imgIdx }));
                                                                            }}
                                                                            className={`w-2 h-2 rounded-full transition-all ${imgIdx === imgIndex ? 'bg-white' : 'bg-white/40'}`}
                                                                        />
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Content - Simplified like Mountain Shadows */}
                                                        <div className={`p-6 ${theme.bgCard}`}>
                                                            <h3 className={`text-xl md:text-2xl font-extrabold ${theme.textPrimary} mb-2 leading-tight`}>
                                                                {pkg.title}
                                                            </h3>
                                                            {pkg.duration && (
                                                                <p className={`text-base ${theme.textSecondary} font-medium mb-2`}>
                                                                    {pkg.duration}
                                                                </p>
                                                            )}
                                                            {/* Price */}
                                                            <div className="mb-4 pt-3 border-t border-gray-200">
                                                                <p className={`text-sm ${theme.textSecondary} mb-1`}>Starting from</p>
                                                                <p className={`text-2xl font-extrabold ${theme.textAccent || theme.textPrimary}`}>
                                                                    {formatCurrency(pkg.price || 0)}
                                                                    <span className={`text-sm ${theme.textSecondary} font-normal`}>/package</span>
                                                                </p>
                                                            </div>
                                                            {/* CTA Row */}
                                                            <div className="mt-4 flex items-center justify-between">
                                                                <button
                                                                    type="button"
                                                                    onClick={(e) => { e.stopPropagation(); handleOpenPackageBookingForm(pkg.id); }}
                                                                    className="px-5 py-2 rounded-lg bg-gradient-to-r from-[#d4af37] via-[#f4d03f] to-[#d4af37] text-[#1a472a] font-bold shadow-lg hover:shadow-xl hover:from-[#f4d03f] hover:via-[#ffd700] hover:to-[#f4d03f] border border-[#b8941f] uppercase tracking-wide transition-all duration-300"
                                                                >
                                                                    Book Now
                                                                </button>
                                                                <span className={`text-sm ${theme.textSecondary}`}>
                                                                    Tap card to book
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <p className={`text-center py-12 ${theme.textSecondary}`}>No packages available at the moment.</p>
                            )}
                        </div>
                    </section>

                    {/* Luxury Villa Showcase Section */}
                    <section id="rooms-section" className="bg-gradient-to-b from-white via-[#f4ede1] to-[#efe1ce] py-20 transition-colors duration-500">
                        <div className="w-full mx-auto px-2 sm:px-4 md:px-6">
                            {/* Section Header */}
                            <div className="text-center mb-16">
                                <span className="inline-block px-6 py-2 bg-[#0f5132]/10 text-[#0f5132] text-sm font-semibold tracking-[0.35em] uppercase rounded-full border border-[#d8c9ac] mb-4">
                                    ✦ LUXURY ACCOMMODATION ✦
                                </span>
                                <h2 className={`text-4xl md:text-5xl font-extrabold ${theme.textPrimary} mb-4`}>
                                    Sustainable Luxury Cottages with Unforgettable Views
                                </h2>
                                <p className={`text-lg ${theme.textSecondary} max-w-3xl mx-auto leading-relaxed`}>
                                    Experience the perfect blend of luxury and sustainability in our eco-friendly cottages with panoramic lake and forest views
                                </p>
                            </div>

                            {/* Info Banner - Show when dates not selected */}
                            {(!bookingData.check_in || !bookingData.check_out) && (
                                <div className="mb-8">
                                    <div className={`inline-block w-full p-4 ${theme.bgSecondary} rounded-xl border ${theme.border} shadow-sm`}>
                                        <div className="flex items-center gap-3 justify-center flex-wrap">
                                            <BedDouble className={`w-5 h-5 ${theme.textAccent}`} />
                                            <p className={`text-sm ${theme.textSecondary}`}>
                                                Select check-in and check-out dates above to check room availability for your stay
                                            </p>
                                            <button
                                                onClick={() => { setShowAmenities(false); setIsGeneralBookingOpen(true); }}
                                                className={`px-4 py-2 text-xs font-semibold ${theme.buttonBg} ${theme.buttonText} rounded-full shadow hover:shadow-md transition-all duration-300 transform hover:scale-105`}
                                            >
                                                Select Dates
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Availability Info - Show when dates are selected */}
                            {bookingData.check_in && bookingData.check_out && Object.keys(roomAvailability).length > 0 && (
                                <div className="mb-6">
                                    <div className={`inline-block w-full p-3 ${theme.bgCard} rounded-lg border ${theme.border} shadow-sm`}>
                                        <p className={`text-sm ${theme.textPrimary} text-center`}>
                                            Showing availability for <span className="font-semibold">{bookingData.check_in}</span> to <span className="font-semibold">{bookingData.check_out}</span>
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Villa Grid - Always show ALL rooms */}
                            {rooms.length > 0 ? (
                                <>
                                    <div className="mb-4 text-center">
                                        <p className={`text-sm ${theme.textSecondary}`}>
                                            Showing all <span className="font-semibold ${theme.textPrimary}">{rooms.length}</span> rooms
                                        </p>
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                                        {rooms.map((room, index) => (
                                            <div
                                                key={room.id}
                                                className={`group relative ${theme.bgCard} rounded-2xl overflow-hidden luxury-shadow transition-all duration-300 transition-all duration-500 transform hover:-translate-y-2 border ${theme.cardBorder || theme.border}`}
                                            >
                                                {/* Image Container with Overlay */}
                                                <div className="relative h-48 overflow-hidden">
                                                    <img
                                                        src={getImageUrl(room.image_url)}
                                                        alt={room.type}
                                                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                                        onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                    />
                                                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />

                                                    {/* Luxury Badge */}
                                                    <div className="absolute top-4 left-4">
                                                        <span className="px-4 py-2 bg-gradient-to-r from-[#0f5132] to-[#1a7042] text-white text-xs font-semibold uppercase tracking-[0.3em] rounded-full shadow-lg">
                                                            Premium Villa
                                                        </span>
                                                    </div>

                                                    {/* Availability Badge - Only show when dates are selected */}
                                                    {bookingData.check_in && bookingData.check_out && (
                                                        <div className="absolute top-4 right-4">
                                                            {roomAvailability[room.id] ? (
                                                                <span className="px-4 py-2 rounded-full text-xs font-bold shadow-lg bg-green-500 text-white">
                                                                    Available
                                                                </span>
                                                            ) : (
                                                                <span className="px-4 py-2 rounded-full text-xs font-bold shadow-lg bg-red-500 text-white">
                                                                    Booked
                                                                </span>
                                                            )}
                                                        </div>
                                                    )}

                                                    {/* Hover Effect Overlay */}
                                                    <div className="absolute inset-0 bg-transparent group-hover:bg-[#0f5132]/10 transition-all duration-500" />
                                                </div>

                                                {/* Content */}
                                                <div className="p-4 space-y-4">
                                                    <h3 className={`text-2xl font-bold ${theme.textCardPrimary || theme.textPrimary} group-hover:${theme.textCardAccent || theme.textAccent} transition-colors`}>
                                                        {room.type}
                                                    </h3>
                                                    <div className={`flex items-center gap-2 text-sm ${theme.textCardSecondary || theme.textSecondary}`}>
                                                        <BedDouble className={`w-5 h-5 ${theme.textCardAccent || theme.textAccent}`} />
                                                        <span>Room #{room.number}</span>
                                                    </div>

                                                    {/* Features */}
                                                    {(room.air_conditioning || room.wifi || room.bathroom || room.living_area || room.terrace || room.parking || room.kitchen || room.family_room || room.bbq || room.garden || room.dining || room.breakfast) && (
                                                        <div className="flex flex-wrap items-center gap-2 text-sm mt-2">
                                                            {room.air_conditioning && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                                                                    AC
                                                                </span>
                                                            )}
                                                            {room.wifi && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                                                    WiFi
                                                                </span>
                                                            )}
                                                            {room.bathroom && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                                                                    Bathroom
                                                                </span>
                                                            )}
                                                            {room.living_area && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                                                                    Living
                                                                </span>
                                                            )}
                                                            {room.terrace && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                                                                    Terrace
                                                                </span>
                                                            )}
                                                            {room.parking && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-indigo-500"></span>
                                                                    Parking
                                                                </span>
                                                            )}
                                                            {room.kitchen && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-pink-100 text-pink-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-pink-500"></span>
                                                                    Kitchen
                                                                </span>
                                                            )}
                                                            {room.family_room && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-teal-100 text-teal-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-teal-500"></span>
                                                                    Family
                                                                </span>
                                                            )}
                                                            {room.bbq && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-red-500"></span>
                                                                    BBQ
                                                                </span>
                                                            )}
                                                            {room.garden && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                                                    Garden
                                                                </span>
                                                            )}
                                                            {room.dining && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                                                                    Dining
                                                                </span>
                                                            )}
                                                            {room.breakfast && (
                                                                <span className="flex items-center gap-1 px-2 py-1 bg-cyan-100 text-cyan-700 rounded-full text-xs">
                                                                    <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
                                                                    Breakfast
                                                                </span>
                                                            )}
                                                        </div>
                                                    )}

                                                    {/* Price */}
                                                    <div className={`flex items-baseline justify-between pt-2 border-t ${theme.cardBorder || theme.border}`}>
                                                        <div>
                                                            <p className={`text-sm ${theme.textCardSecondary || theme.textSecondary}`}>Starting from</p>
                                                            <p className={`text-3xl font-extrabold ${theme.textCardAccent || theme.textAccent}`}>
                                                                {formatCurrency(room.price)}
                                                                <span className={`text-sm ${theme.textCardSecondary || theme.textSecondary} font-normal`}>/night</span>
                                                            </p>
                                                        </div>
                                                    </div>

                                                    {/* CTA Button */}
                                                    <button
                                                        onClick={() => handleOpenRoomBookingForm(room.id)}
                                                        disabled={bookingData.check_in && bookingData.check_out && !roomAvailability[room.id]}
                                                        className={`w-full mt-4 px-6 py-3 font-bold rounded-lg shadow-lg transition-all duration-300 transform hover:scale-105 flex items-center justify-center gap-2 uppercase tracking-wider ${bookingData.check_in && bookingData.check_out && !roomAvailability[room.id]
                                                            ? 'bg-gray-400 text-gray-700 cursor-not-allowed opacity-50'
                                                            : 'bg-gradient-to-r from-[#d4af37] via-[#f4d03f] to-[#d4af37] text-[#1a472a] border-2 border-[#b8941f] hover:from-[#f4d03f] hover:via-[#ffd700] hover:to-[#f4d03f] hover:shadow-[0_0_30px_rgba(212,175,55,0.6)]'
                                                            }`}
                                                    >
                                                        {bookingData.check_in && bookingData.check_out && !roomAvailability[room.id] ? 'Not Available' : 'Book Now'}
                                                        <ChevronRight className="w-5 h-5" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </>
                            ) : (
                                <div className="text-center py-12">
                                    <BedDouble className={`w-16 h-16 ${theme.textSecondary} mx-auto mb-4`} />
                                    <p className={`text-lg font-semibold ${theme.textPrimary} mb-2`}>No rooms available</p>
                                    <p className={`${theme.textSecondary}`}>No rooms found in the system.</p>
                                </div>
                            )}

                        </div>
                    </section>

                    {/* Signature Experiences Section - Resort Style */}
                    <section className="bg-gradient-to-b from-[#f4ede1] via-[#f9f4ea] to-white py-20 transition-colors duration-500">
                        <div className="w-full mx-auto px-2 sm:px-4 md:px-6">
                            {/* Section Header */}
                            <div className="text-center mb-16">
                                <span className="inline-block px-6 py-2 bg-[#0f5132]/10 text-[#0f5132] text-sm font-semibold tracking-[0.35em] uppercase rounded-full border border-[#d8c9ac] mb-4">
                                    ✦ Signature Experiences ✦
                                </span>
                                <h2 className={`text-4xl md:text-5xl font-extrabold ${theme.textPrimary} mb-4`}>
                                    SIGNATURE EXPERIENCES AT THE BEST LUXURY RESORT
                                </h2>
                                <p className={`text-lg ${theme.textSecondary} max-w-3xl mx-auto leading-relaxed`}>
                                    Guests can enjoy a range of curated in-house activities designed to explore the region's rich flora and fauna
                                </p>
                            </div>

                            {totalSignatureExperiences > 0 ? (
                                <div className="relative max-w-6xl mx-auto">
                                    {/* Carousel Container */}
                                    <div className="relative h-[400px] sm:h-[460px] lg:h-[520px]">
                                        {[-2, -1, 0, 1, 2].map((offset) => {
                                            if (totalSignatureExperiences === 1 && offset !== 0) return null;
                                            const experience = totalSignatureExperiences
                                                ? activeSignatureExperiences[(signatureIndex + offset + totalSignatureExperiences) % totalSignatureExperiences]
                                                : null;
                                            if (!experience) return null;

                                            const style = getSignatureCardStyle(offset);
                                            const highlights = (experience.description || '')
                                                .split(/[\n•\.]/)
                                                .map(item => item.trim())
                                                .filter(Boolean)
                                                .slice(0, 3);

                                            return (
                                                <div
                                                    key={`${experience.id}-${offset}`}
                                                    className="absolute top-1/2 left-1/2 w-[72%] sm:w-[60%] lg:w-[50%] max-w-xl transition-all duration-700 ease-[cubic-bezier(.4,.0,.2,1)] will-change-transform"
                                                    style={{
                                                        ...style,
                                                        pointerEvents: offset === 0 ? 'auto' : 'none'
                                                    }}
                                                >
                                                    <div
                                                        className={`relative group h-[400px] sm:h-[460px] lg:h-[520px] rounded-[32px] overflow-hidden bg-black shadow-[0_35px_80px_rgba(12,61,38,0.35)] transition-transform duration-700 ease-[cubic-bezier(.4,.0,.2,1)] will-change-transform ${offset === 0 ? '' : 'scale-[0.9] opacity-70 blur-[1.5px]'}`}
                                                    >
                                                        <img
                                                            src={getImageUrl(experience.image_url)}
                                                            alt={experience.title}
                                                            className="absolute inset-0 w-full h-full object-cover transition-transform duration-[1500ms] ease-out group-hover:scale-[1.12]"
                                                            onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                        />
                                                        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/90 via-black/60 to-transparent" />
                                                        <div className="absolute top-6 left-6 z-10">
                                                            <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.35em] text-white/95 bg-white/20 border border-white/30 rounded-full px-5 py-1.5 shadow-lg backdrop-blur">
                                                                Explore
                                                            </span>
                                                        </div>
                                                        <div className="absolute inset-x-0 bottom-0 z-10 px-8 pb-10 pt-16 space-y-6">
                                                            <h3 className="text-3xl sm:text-4xl font-bold text-white leading-tight drop-shadow-[0_12px_30px_rgba(0,0,0,0.6)]">
                                                                {experience.title}
                                                            </h3>
                                                            {highlights.length > 0 && (
                                                                <ul className="space-y-3 text-base text-white/90">
                                                                    {highlights.map((point, idx) => (
                                                                        <li key={idx} className="flex items-start gap-3">
                                                                            <span className="mt-1 inline-flex w-2.5 h-2.5 rounded-full bg-[#c99c4e]" />
                                                                            <span>{point}</span>
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>

                                    {/* Carousel Controls */}
                                    {totalSignatureExperiences > 1 && (
                                        <>
                                            <button
                                                onClick={() => goToSignature(-1)}
                                                aria-label="Previous experience"
                                                type="button"
                                                className="absolute left-0 top-1/2 -translate-y-1/2 bg-white w-12 h-12 rounded-full shadow-lg border border-[#d6c8ab] flex items-center justify-center hover:scale-105 transition-transform"
                                            >
                                                <ChevronLeft className="w-6 h-6 text-[#0f5132]" />
                                            </button>
                                            <button
                                                onClick={() => goToSignature(1)}
                                                aria-label="Next experience"
                                                type="button"
                                                className="absolute right-0 top-1/2 -translate-y-1/2 bg-white w-12 h-12 rounded-full shadow-lg border border-[#d6c8ab] flex items-center justify-center hover:scale-105 transition-transform"
                                            >
                                                <ChevronRight className="w-6 h-6 text-[#0f5132]" />
                                            </button>
                                        </>
                                    )}

                                    {/* Carousel Indicators */}
                                    {totalSignatureExperiences > 1 && (
                                        <div className="mt-10 flex justify-center gap-2">
                                            {activeSignatureExperiences.map((exp, idx) => (
                                                <button
                                                    key={exp.id}
                                                    onClick={() => setSignatureIndex(idx)}
                                                    type="button"
                                                    className={`w-3 h-3 rounded-full transition-all ${idx === signatureIndex
                                                        ? 'bg-[#0f5132]'
                                                        : 'bg-[#c99c4e]/40 hover:bg-[#c99c4e]/70'
                                                        }`}
                                                    aria-label={`Go to experience ${idx + 1}`}
                                                />
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <p className={`text-center py-12 ${theme.textSecondary}`}>No signature experiences available at the moment.</p>
                            )}
                        </div>
                    </section>

                    {/* Plan Your Wedding Section - Dynamic with Slider */}
                    {planWeddings.length > 0 && planWeddings.some(w => w.is_active) && (
                        <section
                            className="relative w-full h-[600px] md:h-[700px] overflow-hidden"
                            onMouseEnter={() => setIsWeddingHovered(true)}
                            onMouseLeave={() => setIsWeddingHovered(false)}
                        >
                            {planWeddings.filter(w => w.is_active).map((wedding, index) => (
                                <div key={wedding.id}>
                                    {/* Background Images with Animation and Auto-Change */}
                                    <div className="absolute inset-0">
                                        <img
                                            src={getImageUrl(wedding.image_url)}
                                            alt={wedding.title}
                                            className={`absolute inset-0 w-[110%] h-[110%] object-cover object-center transition-all duration-[10000ms] ease-in-out ${index === currentWeddingIndex ? 'opacity-100 scale-100' : 'opacity-0 scale-110'} animate-[slow-pan_20s_ease-in-out_infinite]`}
                                            style={{
                                                animationDelay: `${index * 2}s`,
                                                animationDirection: index % 2 === 0 ? 'alternate' : 'alternate-reverse'
                                            }}
                                            onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                        />
                                        {/* Gradient Overlay */}
                                        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/60 to-black/30"></div>
                                    </div>

                                    {/* Content Overlay */}
                                    <div className={`relative h-full flex items-center justify-center px-4 sm:px-6 lg:px-8 transition-all duration-1000 ease-in-out ${index === currentWeddingIndex ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                                        <div className="max-w-5xl mx-auto text-center text-white">
                                            {/* Badge */}
                                            <div className="mb-6 inline-block px-6 py-2 bg-white/15 backdrop-blur-sm rounded-full border border-white/40 animate-[fadeInUp_1s_ease-out]">
                                                <span className="text-[#d8b471] text-sm font-semibold tracking-[0.35em] uppercase">
                                                    ✦ Perfect Venue ✦
                                                </span>
                                            </div>

                                            {/* Main Title */}
                                            <h2 className="text-3xl md:text-5xl lg:text-7xl font-extrabold mb-6 animate-[fadeInUp_1.2s_ease-out] drop-shadow-2xl leading-tight">
                                                {wedding.title.split(' ').slice(0, 3).join(' ')}<br />
                                                <span className="bg-gradient-to-r from-white via-[#f5e6c9] to-white bg-clip-text text-transparent">
                                                    {wedding.title.split(' ').slice(3).join(' ') || 'WEDDING DESTINATION'}
                                                </span>
                                            </h2>

                                            {/* Description */}
                                            <p className="text-base md:text-xl lg:text-2xl text-white/90 max-w-4xl mx-auto leading-relaxed mb-8 animate-[fadeInUp_1.4s_ease-out] drop-shadow-lg">
                                                {wedding.description}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {/* Navigation Dots */}
                            {planWeddings.filter(w => w.is_active).length > 1 && (
                                <div className="absolute bottom-4 md:bottom-8 left-1/2 transform -translate-x-1/2 flex gap-2 z-20">
                                    {planWeddings.filter(w => w.is_active).map((_, index) => (
                                        <button
                                            key={index}
                                            onClick={() => setCurrentWeddingIndex(index)}
                                            className={`transition-all duration-300 ${index === currentWeddingIndex
                                                ? "w-12 h-1 bg-[#d8b471] rounded-full shadow-[0_0_12px_rgba(216,180,113,0.6)]"
                                                : "w-8 h-1 bg-white/40 hover:bg-white/70 rounded-full"
                                                }`}
                                            aria-label={`Go to slide ${index + 1}`}
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* Premium Services Showcase Section */}
                    <section data-services-section className={`${theme.bgCard} py-20 transition-colors duration-500`}>
                        <div className="w-full mx-auto px-2 sm:px-4 md:px-6">
                            {/* Section Header */}
                            <div className="text-center mb-16">
                                <span className="inline-block px-6 py-2 bg-[#0f5132]/10 text-[#0f5132] text-sm font-semibold tracking-[0.35em] uppercase rounded-full border border-[#d8c9ac] mb-4">
                                    ✦ Premium Services ✦
                                </span>
                                <h2 className={`text-4xl md:text-5xl font-extrabold ${theme.textPrimary} mb-4`}>
                                    WORLD-CLASS AMENITIES & SERVICES
                                </h2>
                                <p className={`text-lg ${theme.textSecondary} max-w-3xl mx-auto leading-relaxed`}>
                                    Experience unparalleled luxury with our comprehensive range of world-class amenities and personalized services
                                </p>
                            </div>

                            {services.length > 0 ? (
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                                    {services.slice(0, 3).map((service) => (
                                        <div
                                            key={service.id}
                                            className="relative group overflow-hidden rounded-[26px] bg-white shadow-[0_18px_35px_rgba(12,61,38,0.18)] transition-transform duration-500 hover:-translate-y-3"
                                        >
                                            <div className="relative h-64 overflow-hidden">
                                                {service.images && service.images.length > 0 ? (
                                                    <img
                                                        src={getImageUrl(service.images[0].image_url)}
                                                        alt={service.name}
                                                        className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                                        onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                    />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#0f5132]/15 via-[#1a7042]/15 to-[#c99c4e]/20">
                                                        <ConciergeBell className="w-12 h-12 text-[#0f5132]" />
                                                    </div>
                                                )}
                                                <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-black/15 to-transparent" />
                                                <div className="absolute bottom-4 left-0 right-0 px-6 text-white">
                                                    <h3 className="text-3xl md:text-4xl font-extrabold text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.8)] drop-shadow-[0_4px_12px_rgba(0,0,0,0.6)]" style={{ textShadow: '0 0 20px rgba(255,255,255,0.3), 0 2px 8px rgba(0,0,0,0.9), 0 4px 12px rgba(0,0,0,0.7)' }}>{service.name}</h3>
                                                </div>
                                            </div>
                                            <div className="p-6 space-y-4">
                                                <p className="text-sm text-[#4f6f62] leading-relaxed">
                                                    {service.description}
                                                </p>
                                                <button
                                                    type="button"
                                                    onClick={() => handleOpenServiceBookingForm(service.id)}
                                                    className="inline-flex items-center gap-2 text-sm font-semibold text-[#0f5132] hover:text-[#1a7042] transition-colors"
                                                >
                                                    Explore Service
                                                    <ChevronRight className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className={`text-center py-12 ${theme.textSecondary}`}>No services available at the moment.</p>
                            )}
                        </div>
                    </section>

                    {/* Premium Cuisine Section - Mountain Shadows Style */}
                    <section data-food-section className={`bg-gradient-to-b ${theme.bgCard} ${theme.bgSecondary} py-20 pb-28 transition-colors duration-500`}>
                        <div className="w-full mx-auto px-2 sm:px-4 md:px-6">
                            {/* Section Header */}
                            <div className="text-center mb-16">
                                <span className="inline-block px-6 py-2 bg-[#0f5132]/10 text-[#0f5132] text-sm font-semibold tracking-[0.35em] uppercase rounded-full border border-[#d8c9ac] mb-4">
                                    ✦ Savor the Art ✦
                                </span>
                                <h2 className={`text-4xl md:text-5xl font-extrabold ${theme.textPrimary} mb-4`}>
                                    SAVOR THE ART OF CUISINE
                                </h2>
                                <p className={`text-lg ${theme.textSecondary} max-w-3xl mx-auto leading-relaxed`}>
                                    Experience the art of cuisine at our luxury resort. Enjoy a diverse menu featuring international favorites and authentic local flavors, crafted to delight every palate.
                                </p>
                            </div>

                            {foodItems.length > 0 ? (
                                <>
                                    <div className="flex flex-wrap justify-center gap-3 mb-10">
                                        {categoryNames.map((category) => {
                                            const count = category === 'All'
                                                ? foodItems.length
                                                : (foodItemsByCategory[category]?.length || 0);
                                            return (
                                                <button
                                                    key={category}
                                                    type="button"
                                                    onClick={() => setSelectedFoodCategory(category)}
                                                    className={`px-4 py-2 rounded-full text-sm font-semibold transition-all duration-200 flex items-center gap-2 ${selectedFoodCategory === category
                                                        ? 'bg-[#0f5132] text-white shadow'
                                                        : 'bg-white text-[#0f5132] border border-[#d8c9ac] hover:bg-[#0f5132]/10'
                                                        }`}
                                                >
                                                    <span>{category}</span>
                                                    <span className={`text-xs px-2 py-0.5 rounded-full ${selectedFoodCategory === category
                                                        ? 'bg-white/20 text-white'
                                                        : 'bg-[#0f5132]/10 text-[#0f5132]'
                                                        }`}>
                                                        {count}
                                                    </span>
                                                </button>
                                            );
                                        })}
                                    </div>

                                    {displayedFoodItems.length > 0 ? (
                                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                            {displayedFoodItems.map((food) => {
                                                const categoryName = food.category?.name || food.category_name || 'Uncategorized';
                                                return (
                                                    <div
                                                        key={food.id}
                                                        className={`group relative ${theme.bgCard} rounded-2xl overflow-hidden luxury-shadow transition-all duration-300 transform hover:-translate-y-2 border ${theme.cardBorder || theme.border}`}
                                                    >
                                                        <div className="relative h-40 overflow-hidden">
                                                            <img
                                                                src={getImageUrl(food.images?.[0]?.image_url)}
                                                                alt={food.name}
                                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                                                onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                            />
                                                            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                                                            <div className="absolute top-3 left-3 px-3 py-1 bg-black/40 text-white text-xs font-semibold rounded-full backdrop-blur-sm">
                                                                {categoryName}
                                                            </div>
                                                            <div className="absolute top-3 right-3">
                                                                <span className={`px-3 py-1 rounded-full text-xs font-bold shadow-lg ${food.available ? "bg-green-500 text-white" : "bg-red-500 text-white"}`}>
                                                                    {food.available ? "Available" : "Unavailable"}
                                                                </span>
                                                            </div>
                                                        </div>
                                                        <div className="p-5 space-y-2">
                                                            <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[#0f5132]/70 bg-[#0f5132]/10 px-3 py-1 rounded-full">
                                                                {categoryName}
                                                            </span>
                                                            <h4 className={`text-lg font-semibold ${theme.textCardPrimary || theme.textPrimary}`}>
                                                                {food.name}
                                                            </h4>
                                                            {food.price && (
                                                                <p className="text-sm text-[#1a7042] font-semibold">
                                                                    {formatCurrency(food.price)}
                                                                </p>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    ) : (
                                        <div className="text-center py-10 bg-white/60 border border-[#d8c9ac] rounded-2xl">
                                            <p className="text-[#4f6f62] font-medium">
                                                No dishes available under <span className="font-semibold text-[#0f5132]">{selectedFoodCategory}</span> yet.
                                            </p>
                                        </div>
                                    )}
                                </>
                            ) : (
                                <p className={`text-center py-12 ${theme.textSecondary}`}>No food items available at the moment.</p>
                            )}
                        </div>
                    </section>

                    {/* Premium Gallery Section - Mountain Shadows Style */}
                    <section data-gallery-section className={`bg-gradient-to-b ${theme.bgCard} ${theme.bgSecondary} py-20 transition-colors duration-500`}>
                        <div className="w-full mx-auto px-2 sm:px-4 md:px-6">
                            {/* Section Header */}
                            <div className="text-center mb-16">
                                <span className="inline-block px-6 py-2 bg-[#0f5132]/10 text-[#0f5132] text-sm font-semibold tracking-[0.35em] uppercase rounded-full border border-[#d8c9ac] mb-4">
                                    ✦ Captured Moments ✦
                                </span>
                                <h2 className={`text-4xl md:text-5xl font-extrabold ${theme.textPrimary} mb-4`}>
                                    EXPLORE THE TIMELESS BEAUTY
                                </h2>
                                <p className={`text-lg ${theme.textSecondary} max-w-3xl mx-auto leading-relaxed`}>
                                    Witness the charm of our resort's stunning views and unforgettable experiences
                                </p>
                            </div>

                            {/* Gallery Grid */}
                            {galleryImages.length > 0 ? (
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 auto-rows-auto gap-4" style={{ overflow: 'visible' }}>
                                    {galleryImages.map((image, index) => (
                                        <div
                                            key={image.id}
                                            className="group relative overflow-hidden rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 reveal"
                                            style={{ height: getGalleryCardHeight(index), transitionDelay: `${(index % 5) * 70}ms` }}
                                        >
                                            <img
                                                src={getImageUrl(image.image_url)}
                                                alt={image.caption || 'Gallery image'}
                                                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                                loading="lazy"
                                                onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                            />

                                            {/* Overlay on Hover */}
                                            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex items-end justify-center p-6">
                                                {image.caption && (
                                                    <p className="text-white text-lg font-semibold drop-shadow-lg">
                                                        {image.caption}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className={`text-center py-12 ${theme.textSecondary}`}>No gallery images available at the moment.</p>
                            )}

                            {/* View More Button removed: grid now wraps into multiple rows automatically */}
                        </div>
                    </section>

                    {/* Nearby Attractions Feature Banner */}
                    {totalNearbyAttractionBanners > 0 && (
                        <section className="relative w-full h-[520px] md:h-[620px] overflow-hidden rounded-3xl mt-20 mb-10 bg-[#0f5132]/5">
                            {activeNearbyAttractionBanners.map((banner, index) => (
                                <div key={banner.id} className="absolute inset-0">
                                    <img
                                        src={getImageUrl(banner.image_url)}
                                        alt={banner.title}
                                        className={`absolute inset-0 w-full h-full object-cover transition-all duration-[9000ms] ease-in-out ${index === currentAttractionBannerIndex ? 'opacity-100 scale-100' : 'opacity-0 scale-110'}`}
                                        style={{
                                            animationDelay: `${index * 2}s`,
                                            animationDirection: index % 2 === 0 ? 'alternate' : 'alternate-reverse'
                                        }}
                                        onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/60 to-black/20" />
                                </div>
                            ))}
                            {totalNearbyAttractionBanners > 0 && (
                                <div className="relative z-10 h-full flex items-center justify-center px-4 sm:px-6 lg:px-8 text-center text-white">
                                    <div className="max-w-4xl mx-auto space-y-6">
                                        <div className="inline-flex items-center gap-2 px-6 py-2 bg-white/15 backdrop-blur-sm rounded-full border border-white/30 uppercase tracking-[0.35em] text-xs font-semibold">
                                            ✦ Nearby Attractions ✦
                                        </div>
                                        <h2 className="text-3xl md:text-5xl font-extrabold leading-tight drop-shadow-xl">
                                            {activeNearbyAttractionBanners[currentAttractionBannerIndex]?.title || 'Explore the Destination'}
                                        </h2>
                                        <p className="text-base md:text-xl text-white/85 leading-relaxed drop-shadow-lg">
                                            {activeNearbyAttractionBanners[currentAttractionBannerIndex]?.subtitle || 'Discover the most captivating sights surrounding our resort.'}
                                        </p>
                                        {/* Map button displayed in main Nearby Attractions section */}
                                    </div>
                                </div>
                            )}
                            {totalNearbyAttractionBanners > 1 && (
                                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2 z-20">
                                    {activeNearbyAttractionBanners.map((_, index) => (
                                        <button
                                            key={index}
                                            onClick={() => setCurrentAttractionBannerIndex(index)}
                                            className={`transition-all duration-300 ${index === currentAttractionBannerIndex
                                                ? "w-12 h-1 bg-[#d8b471] rounded-full shadow-[0_0_12px_rgba(216,180,113,0.6)]"
                                                : "w-8 h-1 bg-white/40 hover:bg-white/70 rounded-full"
                                                }`}
                                            aria-label={`Show attraction ${index + 1}`}
                                            type="button"
                                        />
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {/* Nearby Attractions Section - Mountain Shadows Style */}
                    {nearbyAttractions.length > 0 && nearbyAttractions.some(a => a.is_active) && (
                        <section className={`bg-gradient-to-b ${theme.bgCard} ${theme.bgSecondary} py-20 transition-colors duration-500`}>
                            <div className="w-full mx-auto px-2 sm:px-4 md:px-6">
                                <div className="text-center mb-16">
                                    <span className="inline-block px-6 py-2 bg-[#0f5132]/10 text-[#0f5132] text-sm font-semibold tracking-[0.35em] uppercase rounded-full border border-[#d8c9ac] mb-4">
                                        ✦ Explore ✦
                                    </span>
                                    <h2 className={`text-4xl md:text-5xl font-extrabold ${theme.textPrimary} mb-4`}>
                                        NEARBY ATTRACTIONS
                                    </h2>
                                </div>

                                {/* Split Layout - Image Left, Text Right or vice versa */}
                                <div className="space-y-12">
                                    {nearbyAttractions.filter(attr => attr.is_active).map((attraction, index) => (
                                        <div
                                            key={attraction.id}
                                            className={`${theme.bgCard} rounded-3xl overflow-hidden shadow-2xl border ${theme.border} transition-all duration-500 hover:shadow-3xl`}
                                        >
                                            <div className={`flex flex-col ${index % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'} items-stretch`}>
                                                {/* Image Section */}
                                                <div className="w-full md:w-1/2 overflow-hidden flex items-center justify-center">
                                                    <img
                                                        src={getImageUrl(attraction.image_url)}
                                                        alt={attraction.title}
                                                        className="w-full h-auto object-contain transition-transform duration-700 hover:scale-105"
                                                        onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                    />
                                                </div>

                                                {/* Content Section */}
                                                <div className={`w-full md:w-1/2 p-8 md:p-12 flex flex-col justify-center ${theme.bgCard}`}>
                                                    <h3 className={`text-3xl md:text-4xl font-extrabold ${theme.textPrimary} mb-4 leading-tight`}>
                                                        {attraction.title}
                                                    </h3>
                                                    <div className="w-20 h-1 bg-gradient-to-r from-[#0f5132] via-[#1a7042] to-[#c99c4e] mb-6"></div>
                                                    <p className={`text-base md:text-lg ${theme.textSecondary} leading-relaxed`}>
                                                        {attraction.description}
                                                    </p>
                                                    {attraction.map_link && (
                                                        <a
                                                            href={formatUrl(attraction.map_link)}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="mt-8 inline-flex items-center gap-3 self-start px-6 py-3 bg-[#0f5132] text-white font-semibold rounded-full shadow-lg hover:shadow-xl transition-all duration-300"
                                                        >
                                                            <span className="flex items-center justify-center w-9 h-9 rounded-full bg-white text-[#0f5132]">
                                                                <SiGooglemaps className="w-5 h-5" />
                                                            </span>
                                                            <span>Open in Google Maps</span>
                                                        </a>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </section>
                    )}


                    {/* Reviews Section */}
                    <section data-reviews-section>
                        <h2 className={`group ${sectionTitleStyle}`}>
                            <Quote className={`inline-block mr-3 mb-1 ${iconStyle}`} /> What Our Guests Say
                        </h2>
                        <div className="w-full overflow-hidden" >
                            <div className="flex gap-4 animate-[auto-scroll-bobbing-reverse_90s_linear_infinite] hover:[animation-play-state:paused]" >
                                {reviews.length > 0 ? [...reviews, ...reviews].map((review, index) => (
                                    <div key={`${review.id}-${index}`} className={`group flex-none w-80 md:w-96 ${theme.bgCard} rounded-2xl p-4 shadow-2xl border ${theme.border}`} >
                                        <div className="flex justify-center mb-4" >
                                            {[...Array(review.rating)].map((_, i) => <Star key={i} className={`w-5 h-5 fill-current ${theme.textAccent}`} />)}
                                            {[...Array(5 - review.rating)].map((_, i) => <Star key={i + review.rating} className={`${theme.textSecondary} w-5 h-5`} />)}
                                        </div>
                                        <p className={`text-sm italic mb-4 ${textSecondary}`} >{`"${review.comment}"`}</p>
                                        <p className={`font-semibold ${textPrimary}`} >- {review.guest_name}</p>
                                    </div>
                                )) : <p className={`flex-none w-full text-center ${textSecondary}`} >No reviews available.</p>}
                            </div >
                        </div>
                    </section>
                </main>

                {/* Floating UI Elements */}
                <button onClick={scrollToTop} className={`fixed bottom-8 right-8 p-3 rounded-full ${theme.buttonBg} ${theme.buttonText} shadow-lg transition-all duration-300 ${showBackToTop ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`} aria-label="Back to Top">
                    <ChevronUp className="w-6 h-6" />
                </button>

                <button onClick={toggleChat} className={`fixed bottom-8 left-8 p-4 rounded-full ${theme.buttonBg} ${theme.buttonText} shadow-lg transition-all duration-300 z-50 ${theme.buttonHover}`} aria-label="Open Chat">
                    <MessageSquare className="w-6 h-6" />
                </button>

                {/* AI Concierge Chat Modal */}
                {isChatOpen && (
                    <div className="fixed inset-0 z-[100] bg-neutral-950/80 backdrop-blur-sm flex items-end justify-center">
                        <div className={`w-full max-w-lg h-3/4 md:h-4/5 ${theme.chatBg} rounded-t-3xl shadow-2xl flex flex-col`}>
                            <div className={`${theme.chatHeaderBg} p-4 rounded-t-3xl flex items-center justify-between border-b ${theme.chatInputBorder}`}>
                                <h3 className="text-lg font-bold flex items-center"><MessageSquare className={`w-5 h-5 mr-2 ${theme.textAccent}`} /> AI Concierge</h3>
                                <button onClick={toggleChat} className={`p-1 rounded-full ${theme.textSecondary} hover:${theme.textPrimary} transition-colors`}><X className="w-6 h-6" /></button>
                            </div>
                            <div ref={chatMessagesRef} className="flex-1 p-4 overflow-y-auto space-y-4">
                                {chatHistory.map((msg, index) => (
                                    <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        <div className={`p-3 rounded-xl max-w-xs md:max-w-md shadow-lg ${msg.role === 'user' ? `${theme.chatUserBg} ${theme.chatUserText} rounded-br-none` : `${theme.chatModelBg} ${theme.chatModelText} rounded-bl-none`}`}>
                                            <p className="text-sm break-words">{msg.parts[0].text}</p>
                                        </div>
                                    </div>
                                ))}
                                {isChatLoading && (
                                    <div className="flex justify-start">
                                        <div className={`p-3 rounded-xl ${theme.chatModelBg} shadow-lg`}>
                                            <div className="flex items-center space-x-2 animate-bounce-dot">
                                                <div className={`w-2 h-2 ${theme.chatLoaderBg} rounded-full`} style={{ animationDelay: '0s' }}></div>
                                                <div className={`w-2 h-2 ${theme.chatLoaderBg} rounded-full`} style={{ animationDelay: '0.2s' }}></div>
                                                <div className={`w-2 h-2 ${theme.chatLoaderBg} rounded-full`} style={{ animationDelay: '0.4s' }}></div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <form onSubmit={handleSendMessage} className={`p-4 border-t ${theme.chatInputBorder} ${theme.chatHeaderBg} flex items-center`}>
                                <input type="text" value={userMessage} onChange={(e) => setUserMessage(e.target.value)} placeholder="Ask me anything..."
                                    className={`flex-1 p-3 rounded-full ${theme.chatInputBg} ${theme.textPrimary} ${theme.chatInputPlaceholder} focus:outline-none focus:ring-2 focus:ring-amber-500`} />
                                <button type="submit" className={`ml-2 p-3 rounded-full ${theme.buttonBg} ${theme.buttonText} ${theme.buttonHover} transition-colors disabled:opacity-50`} disabled={!userMessage.trim() || isChatLoading}>
                                    <Send className="w-5 h-5" />
                                </button>
                            </form>
                        </div>
                    </div>
                )}

                {/* General Booking Modal - Date Selection First */}
                {isGeneralBookingOpen && (
                    <div className="fixed inset-0 z-[100] bg-neutral-950/80 backdrop-blur-sm flex items-center justify-center p-4">
                        <div className={`w-full max-w-md ${theme.bgCard} rounded-3xl shadow-2xl flex flex-col`}>
                            <div className={`p-6 flex items-center justify-between border-b ${theme.border}`}>
                                <h3 className="text-lg font-bold flex items-center"><BedDouble className={`w-5 h-5 mr-2 ${theme.textAccent}`} /> Select Your Dates</h3>
                                <button onClick={() => { setIsGeneralBookingOpen(false); setShowAmenities(false); }} className={`p-1 rounded-full ${theme.textSecondary} hover:${theme.textPrimary} transition-colors`}><X className="w-6 h-6" /></button>
                            </div>
                            <div className="p-6 space-y-4">
                                <p className={`${theme.textSecondary} text-center mb-4`}>Select your check-in and check-out dates to view available rooms</p>
                                <div className="flex space-x-4">
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Check-in Date</label>
                                        <input
                                            type="date"
                                            name="check_in"
                                            value={bookingData.check_in}
                                            onChange={handleRoomBookingChange}
                                            min={new Date().toISOString().split('T')[0]}
                                            required
                                            className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-[#0f5132] transition-colors`}
                                        />
                                    </div>
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Check-out Date</label>
                                        <input
                                            type="date"
                                            name="check_out"
                                            value={bookingData.check_out}
                                            onChange={handleRoomBookingChange}
                                            min={bookingData.check_in || new Date().toISOString().split('T')[0]}
                                            required
                                            className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-[#0f5132] transition-colors`}
                                        />
                                    </div>
                                </div>
                                {bookingData.check_in && bookingData.check_out && (
                                    <div className="pt-4 space-y-3 border-top border-gray-200 dark:border-neutral-700">
                                        <p className={`text-sm ${theme.textSecondary} text-center`}>Continue with booking:</p>
                                        <button
                                            onClick={() => { setIsGeneralBookingOpen(false); setShowAmenities(false); setIsRoomBookingFormOpen(true); }}
                                            className={`w-full py-3 rounded-full ${theme.buttonBg} ${theme.buttonText} font-bold shadow-lg ${theme.buttonHover} transition-colors flex items-center justify-center space-x-2`}
                                        >
                                            <BedDouble className="w-5 h-5" />
                                            <span>Book a Room</span>
                                        </button>
                                        <button
                                            onClick={() => {
                                                setIsGeneralBookingOpen(false);
                                                setShowAmenities(false);
                                                setPackageBookingData(prev => ({
                                                    ...prev,
                                                    check_in: bookingData.check_in || prev.check_in || '',
                                                    check_out: bookingData.check_out || prev.check_out || ''
                                                }));
                                                setIsPackageSelectionOpen(true);
                                            }}
                                            className={`w-full py-3 rounded-full ${theme.buttonBg} ${theme.buttonText} font-bold shadow-lg ${theme.buttonHover} transition-colors flex items-center justify-center space-x-2`}
                                        >
                                            <Package className="w-5 h-5" />
                                            <span>Book a Package</span>
                                        </button>
                                        <button
                                            onClick={() => setShowAmenities(prev => !prev)}
                                            className="w-full py-3 rounded-full bg-white text-[#0f5132] font-bold shadow-lg hover:shadow-xl transition-colors flex items-center justify-center space-x-2 border border-[#d8c9ac]"
                                        >
                                            <Droplet className="w-5 h-5 text-[#0f5132]" />
                                            <span>{showAmenities ? "Hide Amenities" : "View Amenities"}</span>
                                        </button>
                                    </div>
                                )}
                                {showAmenities && (
                                    <div className="mt-4 space-y-3 border-t border-gray-200 dark:border-neutral-700 pt-4">
                                        <h4 className="text-sm font-semibold text-center text-[#0f5132] uppercase tracking-widest">
                                            Resort Amenities
                                        </h4>
                                        {services && services.length > 0 ? (
                                            <div className="max-h-48 overflow-y-auto grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                {services.map((service) => (
                                                    <div
                                                        key={service.id}
                                                        className="flex items-start space-x-3 rounded-2xl bg-white/80 border border-[#d8c9ac] px-4 py-3 shadow-sm"
                                                    >
                                                        <div className="flex-shrink-0 mt-1 text-[#0f5132]">
                                                            <ConciergeBell className="w-5 h-5" />
                                                        </div>
                                                        <div>
                                                            <p className="text-sm font-semibold text-[#0f5132]">{service.name}</p>
                                                            {service.description && (
                                                                <p className="text-xs text-[#4f6f62] mt-1 line-clamp-2">
                                                                    {service.description}
                                                                </p>
                                                            )}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-center text-sm text-[#4f6f62] bg-white/70 rounded-2xl px-4 py-6 border border-dashed border-[#d8c9ac]">
                                                Amenities information will be available soon. Please contact concierge for more details.
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Room Booking Modal */}
                {isRoomBookingFormOpen && (
                    <div className="fixed inset-0 z-[100] bg-neutral-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
                        <div className={`w-full max-w-lg ${theme.bgCard} rounded-3xl shadow-2xl flex flex-col max-h-[90vh] my-8`}>
                            <div className={`p-6 flex items-center justify-between border-b ${theme.border}`}>
                                <h3 className="text-lg font-bold flex items-center"><BedDouble className={`w-5 h-5 mr-2 ${theme.textAccent}`} /> Book a Room</h3>
                                <button onClick={() => setIsRoomBookingFormOpen(false)} className={`p-1 rounded-full ${theme.textSecondary} hover:${theme.textPrimary} transition-colors`}><X className="w-6 h-6" /></button>
                            </div>
                            {/* Error message inside modal */}
                            {bannerMessage.text && bannerMessage.type === 'error' && (
                                <div className={`mx-6 mt-4 p-3 rounded-lg bg-red-100 border border-red-300 text-red-700 text-sm flex items-center`}>
                                    <span className="mr-2">❌</span>
                                    {bannerMessage.text}
                                </div>
                            )}
                            {/* Success message inside modal */}
                            {bannerMessage.text && bannerMessage.type === 'success' && (
                                <div className={`mx-6 mt-4 p-3 rounded-lg bg-green-100 border border-green-300 text-green-700 text-sm flex items-center`}>
                                    <span className="mr-2">✅</span>
                                    {bannerMessage.text}
                                </div>
                            )}
                            <form onSubmit={handleRoomBookingSubmit} className="p-4 space-y-4 overflow-y-auto">
                                {/* Always show editable date inputs */}
                                <div className="flex space-x-4">
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Check-in Date</label>
                                        <input
                                            type="date"
                                            name="check_in"
                                            value={bookingData.check_in || ''}
                                            onChange={handleRoomBookingChange}
                                            min={new Date().toISOString().split('T')[0]}
                                            required
                                            className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-[#0f5132] transition-colors`}
                                        />
                                    </div>
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Check-out Date</label>
                                        <input
                                            type="date"
                                            name="check_out"
                                            value={bookingData.check_out || ''}
                                            onChange={handleRoomBookingChange}
                                            min={bookingData.check_in || new Date().toISOString().split('T')[0]}
                                            required
                                            className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-[#0f5132] transition-colors`}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Available Rooms for Selected Dates</label>
                                    {!bookingData.check_in || !bookingData.check_out ? (
                                        <div className={`p-6 text-center rounded-xl ${theme.bgSecondary} border-2 border-dashed ${theme.border}`}>
                                            <BedDouble className={`w-10 h-10 ${theme.textSecondary} mx-auto mb-3`} />
                                            <p className={`text-sm ${theme.textSecondary}`}>Please select check-in and check-out dates above to see available rooms</p>
                                        </div>
                                    ) : (
                                        <>
                                            <p className={`text-xs ${theme.textSecondary} mb-2`}>Showing rooms available from {bookingData.check_in} to {bookingData.check_out}</p>
                                            <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-48 overflow-y-auto p-3 rounded-xl ${theme.bgSecondary}`}>
                                                {rooms.length > 0 ? (
                                                    rooms.map(room => (
                                                        <div key={room.id} onClick={() => handleRoomSelection(room.id)}
                                                            className={`rounded-lg border-2 cursor-pointer transition-all duration-200 overflow-hidden ${bookingData.room_ids.includes(room.id) ? `${theme.buttonBg} ${theme.buttonText} border-transparent` : `${theme.bgCard} ${theme.textPrimary} ${theme.border} hover:border-[#c99c4e]`}`}
                                                        >
                                                            <img
                                                                src={getImageUrl(room.image_url)}
                                                                alt={room.type}
                                                                className="w-full h-20 object-cover"
                                                                onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                            />
                                                            <div className="p-2 text-center">
                                                                <p className="font-semibold text-xs">Room {room.number}</p>
                                                                <p className="text-xs opacity-80">{room.type}</p>
                                                                <p className="text-xs opacity-60 mt-1">Max: {room.adults}A, {room.children}C</p>
                                                                <p className="text-xs font-bold mt-1">{formatCurrency(room.price)}</p>
                                                            </div>
                                                        </div>
                                                    ))
                                                ) : (
                                                    <div className="col-span-full text-center py-8 text-gray-500">
                                                        <BedDouble className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                                        <p className="text-sm font-semibold mb-1">No rooms available</p>
                                                        <p className="text-xs">No rooms are available for the selected dates. Please try different dates.</p>
                                                    </div>
                                                )}
                                            </div>
                                        </>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Full Name</label>
                                    <input type="text" name="guest_name" value={bookingData.guest_name} onChange={handleRoomBookingChange} placeholder="Enter your full name" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Email Address</label>
                                    <input type="email" name="guest_email" value={bookingData.guest_email} onChange={handleRoomBookingChange} placeholder="user@example.com" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Phone Number</label>
                                    <input type="tel" name="guest_mobile" value={bookingData.guest_mobile} onChange={handleRoomBookingChange} placeholder="Enter your mobile number" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="flex space-x-4">
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Adults</label>
                                        <input type="number" name="adults" value={bookingData.adults} onChange={handleRoomBookingChange} min="1" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                    </div>
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Children</label>
                                        <input type="number" name="children" value={bookingData.children} onChange={handleRoomBookingChange} min="0" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                    </div>
                                </div>
                                <button type="submit" className={`w-full py-3 rounded-full ${theme.buttonBg} ${theme.buttonText} font-bold shadow-lg ${theme.buttonHover} transition-colors disabled:opacity-50`} disabled={isBookingLoading}>
                                    {isBookingLoading ? 'Booking...' : 'Confirm Booking'}
                                </button>
                                {bookingMessage.text && (
                                    <div className={`mt-4 p-3 rounded-xl text-center ${bookingMessage.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                                        {bookingMessage.text}
                                    </div>
                                )}
                            </form>
                        </div>
                    </div>
                )}

                {/* Package Booking Modal */}
                {isPackageBookingFormOpen && (
                    <div className="fixed inset-0 z-[100] bg-neutral-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
                        <div className={`w-full max-w-lg ${theme.bgCard} rounded-3xl shadow-2xl flex flex-col max-h-[90vh] my-8`}>
                            <div className={`p-6 flex items-center justify-between border-b ${theme.border}`}>
                                <h3 className="text-lg font-bold flex items-center"><Package className={`w-5 h-5 mr-2 ${theme.textAccent}`} /> Book a Package</h3>
                                <button onClick={() => setIsPackageBookingFormOpen(false)} className={`p-1 rounded-full ${theme.textSecondary} hover:${theme.textPrimary} transition-colors`}><X className="w-6 h-6" /></button>
                            </div>
                            {/* Error message inside modal */}
                            {bannerMessage.text && bannerMessage.type === 'error' && (
                                <div className={`mx-6 mt-4 p-3 rounded-lg bg-red-100 border border-red-300 text-red-700 text-sm flex items-center`}>
                                    <span className="mr-2">❌</span>
                                    {bannerMessage.text}
                                </div>
                            )}
                            {/* Success message inside modal */}
                            {bannerMessage.text && bannerMessage.type === 'success' && (
                                <div className={`mx-6 mt-4 p-3 rounded-lg bg-green-100 border border-green-300 text-green-700 text-sm flex items-center`}>
                                    <span className="mr-2">✅</span>
                                    {bannerMessage.text}
                                </div>
                            )}
                            <form onSubmit={handlePackageBookingSubmit} className="p-4 space-y-4 overflow-y-auto">
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Package ID</label>
                                    <input type="number" name="package_id" value={packageBookingData.package_id || ''} readOnly className={`w-full p-3 rounded-xl ${theme.placeholderBg} ${theme.placeholderText} focus:outline-none`} />
                                </div>
                                {/* Always show editable date inputs */}
                                <div className="flex space-x-4">
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Check-in Date</label>
                                        <input
                                            type="date"
                                            name="check_in"
                                            value={packageBookingData.check_in || ''}
                                            onChange={handlePackageBookingChange}
                                            min={new Date().toISOString().split('T')[0]}
                                            required
                                            className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`}
                                        />
                                    </div>
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Check-out Date</label>
                                        <input
                                            type="date"
                                            name="check_out"
                                            value={packageBookingData.check_out || ''}
                                            onChange={handlePackageBookingChange}
                                            min={packageBookingData.check_in || new Date().toISOString().split('T')[0]}
                                            required
                                            className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`}
                                        />
                                    </div>
                                </div>
                                {/* Room Selection - Only show for room_type packages */}
                                {(() => {
                                    const selectedPackage = packages.find(p => p.id === packageBookingData.package_id);

                                    if (!selectedPackage) {
                                        return null;
                                    }

                                    // Determine if it's whole_property:
                                    // 1. If booking_type is explicitly 'whole_property'
                                    // 2. If booking_type is not set AND room_types is not set (legacy whole_property)
                                    // 3. If booking_type is null/undefined and room_types is null/undefined/empty
                                    const hasRoomTypes = selectedPackage.room_types && selectedPackage.room_types.trim().length > 0;
                                    const isWholeProperty = selectedPackage.booking_type === 'whole_property' ||
                                        selectedPackage.booking_type === 'whole property' ||
                                        (!selectedPackage.booking_type && !hasRoomTypes);

                                    // Show room selection for both room_type and whole_property packages
                                    return (
                                        <div className="space-y-2">
                                            <label className={`block text-sm font-medium ${theme.textSecondary}`}>
                                                {isWholeProperty ? 'Available Rooms (Full Property Booking)' : 'Available Rooms for Selected Dates'}
                                            </label>
                                            {!packageBookingData.check_in || !packageBookingData.check_out ? (
                                                <div className={`p-6 text-center rounded-xl ${theme.bgSecondary} border-2 border-dashed ${theme.border}`}>
                                                    <BedDouble className={`w-10 h-10 ${theme.textSecondary} mx-auto mb-3`} />
                                                    <p className={`text-sm ${theme.textSecondary}`}>Please select check-in and check-out dates above to see available rooms</p>
                                                </div>
                                            ) : (
                                                <>
                                                    {isWholeProperty && (
                                                        <div className={`p-3 rounded-xl ${theme.bgSecondary} border-2 border-amber-300 mb-3`}>
                                                            <p className={`text-sm font-semibold ${theme.textPrimary}`}>Whole Property Package</p>
                                                            <p className={`text-xs ${theme.textSecondary} mt-1`}>
                                                                All available rooms will be booked for the selected dates. You can see them below.
                                                            </p>
                                                        </div>
                                                    )}
                                                    <p className={`text-xs ${theme.textSecondary} mb-2`}>Showing rooms available from {packageBookingData.check_in} to {packageBookingData.check_out}</p>
                                                    <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-48 overflow-y-auto p-3 rounded-xl ${theme.bgSecondary}`}>
                                                        {(() => {
                                                            // Filter rooms based on package type
                                                            let roomsToShow = rooms;

                                                            if (isWholeProperty) {
                                                                // For whole_property: Show ALL available rooms
                                                                roomsToShow = rooms;
                                                            } else if (selectedPackage && selectedPackage.room_types) {
                                                                // For room_type: Only show rooms matching the package's room_types
                                                                const allowedRoomTypes = selectedPackage.room_types.split(',').map(t => t.trim().toLowerCase());
                                                                roomsToShow = rooms.filter(room => {
                                                                    const roomType = room.type ? room.type.trim().toLowerCase() : '';
                                                                    return allowedRoomTypes.includes(roomType);
                                                                });
                                                            } else {
                                                                // Invalid package type - no room_types specified and not whole_property
                                                                return (
                                                                    <div className="col-span-full text-center py-8 text-gray-500">
                                                                        <BedDouble className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                                                        <p className="text-sm font-semibold mb-1">Invalid package type</p>
                                                                        <p className="text-xs">Please select a valid package.</p>
                                                                    </div>
                                                                );
                                                            }

                                                            // Filter to only show available rooms (check availability)
                                                            roomsToShow = roomsToShow.filter(room => {
                                                                // Check if room is available based on packageRoomAvailability
                                                                const isAvailable = packageRoomAvailability[room.id] === true;
                                                                return isAvailable;
                                                            });

                                                            return roomsToShow.length > 0 ? (
                                                                roomsToShow.map(room => {
                                                                    // For whole_property, all available rooms are auto-selected, but still show them
                                                                    const isSelected = packageBookingData.room_ids.includes(room.id);
                                                                    return (
                                                                        <div
                                                                            key={room.id}
                                                                            onClick={() => !isWholeProperty ? handlePackageRoomSelection(room.id) : null}
                                                                            className={`rounded-lg border-2 transition-all duration-200 overflow-hidden ${!isWholeProperty ? 'cursor-pointer' : 'cursor-default'} ${isSelected ? `${theme.buttonBg} ${theme.buttonText} border-transparent` : `${theme.bgCard} ${theme.textPrimary} ${theme.border} ${!isWholeProperty ? 'hover:border-[#c99c4e]' : ''}`}`}
                                                                        >
                                                                            <img
                                                                                src={getImageUrl(room.image_url)}
                                                                                alt={room.type}
                                                                                className="w-full h-20 object-cover"
                                                                                onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                                            />
                                                                            <div className="p-2 text-center">
                                                                                <p className="font-semibold text-xs">Room {room.number}</p>
                                                                                <p className="text-xs opacity-80">{room.type}</p>
                                                                                <p className="text-xs opacity-60 mt-1">Max: {room.adults}A, {room.children}C</p>
                                                                                <p className="text-xs font-bold mt-1">{formatCurrency(room.price)}</p>
                                                                                {isWholeProperty && isSelected && (
                                                                                    <p className="text-xs font-semibold mt-1 text-green-600">✓ Selected</p>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                    );
                                                                })
                                                            ) : (
                                                                <div className="col-span-full text-center py-8 text-gray-500">
                                                                    <BedDouble className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                                                    <p className="text-sm font-semibold mb-1">No rooms available</p>
                                                                    <p className="text-xs">No rooms are available for the selected dates. Please try different dates.</p>
                                                                </div>
                                                            );
                                                        })()}
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    );
                                })()}
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Full Name</label>
                                    <input type="text" name="guest_name" value={packageBookingData.guest_name} onChange={handlePackageBookingChange} placeholder="Enter your full name" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Email Address</label>
                                    <input type="email" name="guest_email" value={packageBookingData.guest_email || ''} onChange={handlePackageBookingChange} placeholder="user@example.com (optional)" className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Phone Number</label>
                                    <input type="tel" name="guest_mobile" value={packageBookingData.guest_mobile} onChange={handlePackageBookingChange} placeholder="Enter your mobile number" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="flex space-x-4">
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Adults</label>
                                        <input type="number" name="adults" value={packageBookingData.adults} onChange={handlePackageBookingChange} min="1" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                    </div>
                                    <div className="space-y-2 w-1/2">
                                        <label className={`block text-sm font-medium ${theme.textSecondary}`}>Children</label>
                                        <input type="number" name="children" value={packageBookingData.children} onChange={handlePackageBookingChange} min="0" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Food Preferences / Food Orders</label>
                                    <textarea name="food_preferences" value={packageBookingData.food_preferences} onChange={handlePackageBookingChange} placeholder="Order your food or mention dietary needs..." className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} rows="2" />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Special Requests (Stay)</label>
                                    <textarea name="special_requests" value={packageBookingData.special_requests} onChange={handlePackageBookingChange} placeholder="Mention any special needs for your stay..." className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} rows="2" />
                                </div>
                                <button type="submit" className={`w-full py-3 rounded-full ${theme.buttonBg} ${theme.buttonText} font-bold shadow-lg ${theme.buttonHover} transition-colors disabled:opacity-50`} disabled={isBookingLoading}>
                                    {isBookingLoading ? 'Booking...' : 'Confirm Booking'}
                                </button>
                                {bookingMessage.text && (
                                    <div className={`mt-4 p-3 rounded-xl text-center ${bookingMessage.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                                        {bookingMessage.text}
                                    </div>
                                )}
                            </form>
                        </div>
                    </div>
                )}

                {/* Package Selection Modal */}
                {isPackageSelectionOpen && (
                    <div className="fixed inset-0 z-[100] bg-neutral-950/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
                        <div className={`w-full max-w-4xl ${theme.bgCard} rounded-3xl shadow-2xl flex flex-col max-h-[90vh] my-8`}>
                            <div className={`p-6 flex items-center justify-between border-b ${theme.border}`}>
                                <h3 className="text-lg font-bold flex items-center"><Package className={`w-5 h-5 mr-2 ${theme.textAccent}`} /> Select a Package</h3>
                                <button onClick={() => setIsPackageSelectionOpen(false)} className={`p-1 rounded-full ${theme.textSecondary} hover:${theme.textPrimary} transition-colors`}><X className="w-6 h-6" /></button>
                            </div>
                            <div className="p-6 overflow-y-auto">
                                {packages.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        {packages.map((pkg) => {
                                            const imgIndex = packageImageIndex[pkg.id] || 0;
                                            const currentImage = pkg.images && pkg.images[imgIndex];
                                            return (
                                                <div
                                                    key={pkg.id}
                                                    onClick={() => {
                                                        handleOpenPackageBookingForm(pkg.id);
                                                        setIsPackageSelectionOpen(false);
                                                    }}
                                                    className={`${theme.bgCard} rounded-2xl overflow-hidden shadow-xl hover:shadow-2xl transition-all duration-500 border ${theme.border} cursor-pointer transform hover:-translate-y-1`}
                                                >
                                                    {/* Image Container */}
                                                    <div className="relative h-48 overflow-hidden">
                                                        <img
                                                            src={currentImage ? getImageUrl(currentImage.image_url) : ITEM_PLACEHOLDER}
                                                            alt={pkg.title}
                                                            className="w-full h-full object-cover transition-transform duration-700 hover:scale-110"
                                                            onError={(e) => { e.target.src = ITEM_PLACEHOLDER; }}
                                                        />
                                                        {/* Image Slider Dots */}
                                                        {pkg.images && pkg.images.length > 1 && (
                                                            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-black/60 backdrop-blur-sm px-3 py-2 rounded-full z-10">
                                                                {pkg.images.map((_, imgIdx) => (
                                                                    <button
                                                                        key={imgIdx}
                                                                        onClick={(e) => {
                                                                            e.stopPropagation();
                                                                            setPackageImageIndex(prev => ({ ...prev, [pkg.id]: imgIdx }));
                                                                        }}
                                                                        className={`w-2 h-2 rounded-full transition-all ${imgIdx === imgIndex ? 'bg-white' : 'bg-white/40'}`}
                                                                    />
                                                                ))}
                                                            </div>
                                                        )}
                                                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent" />
                                                    </div>

                                                    {/* Content */}
                                                    <div className="p-5">
                                                        <h3 className={`text-xl font-bold ${theme.textCardPrimary || theme.textPrimary} mb-2 line-clamp-2`}>
                                                            {pkg.title}
                                                        </h3>
                                                        <p className={`text-sm ${theme.textCardSecondary || theme.textSecondary} mb-3 line-clamp-2`}>
                                                            {pkg.description}
                                                        </p>
                                                        {pkg.complimentary && (
                                                            <div className="mb-3 px-3 py-2 bg-amber-50/50 rounded-lg border border-amber-100">
                                                                <p className={`text-xs ${theme.textAccent} font-semibold uppercase tracking-wide mb-1`}>Includes:</p>
                                                                <p className={`text-xs ${theme.textCardSecondary || theme.textSecondary} line-clamp-2`}>{pkg.complimentary}</p>
                                                            </div>
                                                        )}
                                                        <div className={`flex items-center justify-between pt-3 border-t ${theme.cardBorder || theme.border}`}>
                                                            <span className={`text-2xl font-extrabold ${theme.textCardAccent || theme.textAccent}`}>
                                                                {formatCurrency(pkg.price || 0)}
                                                            </span>
                                                            <button
                                                                className={`px-6 py-2 text-sm font-bold ${theme.buttonBg} ${theme.buttonText} rounded-full shadow-lg ${theme.buttonHover} transition-all duration-300 transform hover:scale-105`}
                                                            >
                                                                Select
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <div className="text-center py-12">
                                        <Package className={`w-16 h-16 ${theme.textSecondary} mx-auto mb-4`} />
                                        <p className={`${theme.textSecondary}`}>No packages available at the moment.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Service Booking Modal */}
                {isServiceBookingFormOpen && (
                    <div className="fixed inset-0 z-[100] bg-neutral-950/80 backdrop-blur-sm flex items-center justify-center p-4">
                        <div className={`w-full max-w-lg ${theme.bgCard} rounded-3xl shadow-2xl flex flex-col`}>
                            <div className={`p-6 flex items-center justify-between border-b ${theme.border}`}>
                                <h3 className="text-lg font-bold flex items-center"><ConciergeBell className={`w-5 h-5 mr-2 ${theme.textAccent}`} /> Book a Service</h3>
                                <button onClick={() => setIsServiceBookingFormOpen(false)} className={`p-1 rounded-full ${theme.textSecondary} hover:${theme.textPrimary} transition-colors`}><X className="w-6 h-6" /></button>
                            </div>
                            <form onSubmit={handleServiceBookingSubmit} className="p-4 space-y-4">
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Service ID</label>
                                    <input type="number" name="service_id" value={serviceBookingData.service_id || ''} readOnly className={`w-full p-3 rounded-xl ${theme.placeholderBg} ${theme.placeholderText} focus:outline-none`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Full Name</label>
                                    <input type="text" name="guest_name" value={serviceBookingData.guest_name} onChange={handleServiceBookingChange} placeholder="Enter your full name" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Email Address</label>
                                    <input type="email" name="guest_email" value={serviceBookingData.guest_email} onChange={handleServiceBookingChange} placeholder="user@example.com" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Phone Number</label>
                                    <input type="tel" name="guest_mobile" value={serviceBookingData.guest_mobile} onChange={handleServiceBookingChange} placeholder="Enter your mobile number" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Room ID (Optional)</label>
                                    <input type="number" name="room_id" value={serviceBookingData.room_id || ''} onChange={handleServiceBookingChange} placeholder="Enter your room ID if assigned" className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <button type="submit" className={`w-full py-3 rounded-full ${theme.buttonBg} ${theme.buttonText} font-bold shadow-lg ${theme.buttonHover} transition-colors disabled:opacity-50`} disabled={isBookingLoading}>
                                    {isBookingLoading ? 'Booking...' : 'Confirm Booking'}
                                </button>
                                {bookingMessage.text && (
                                    <div className={`mt-4 p-3 rounded-xl text-center ${bookingMessage.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                                        {bookingMessage.text}
                                    </div>
                                )}
                            </form>
                        </div>
                    </div>
                )}

                {/* Food Order Modal */}
                {isFoodOrderFormOpen && (
                    <div className="fixed inset-0 z-[100] bg-neutral-950/80 backdrop-blur-sm flex items-center justify-center p-4">
                        <div className={`w-full max-w-lg ${theme.bgCard} rounded-3xl shadow-2xl flex flex-col`}>
                            <div className={`p-6 flex items-center justify-between border-b ${theme.border}`}>
                                <h3 className="text-lg font-bold flex items-center"><Coffee className={`w-5 h-5 mr-2 ${theme.textAccent}`} /> Place a Food Order</h3>
                                <button onClick={() => setIsFoodOrderFormOpen(false)} className={`p-1 rounded-full ${theme.textSecondary} hover:${theme.textPrimary} transition-colors`}><X className="w-6 h-6" /></button>
                            </div>
                            <form onSubmit={handleFoodOrderSubmit} className="p-4 space-y-4">
                                <div className="space-y-2">
                                    <label className={`block text-sm font-medium ${theme.textSecondary}`}>Room ID</label>
                                    <input type="number" name="room_id" value={foodOrderData.room_id || ''} onChange={(e) => setFoodOrderData(prev => ({ ...prev, room_id: parseInt(e.target.value) || '' }))} placeholder="Enter your room ID" required className={`w-full p-3 rounded-xl ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors`} />
                                </div>
                                <h4 className={`text-md font-semibold ${theme.textPrimary}`}>Select Items:</h4>
                                <div className="space-y-4 max-h-60 overflow-y-auto">
                                    {foodItems.map(item => (
                                        <div key={item.id} className="flex items-center justify-between">
                                            <div className="flex items-center space-x-4">
                                                <img src={getImageUrl(item.images?.[0]?.image_url)} alt={item.name} className="w-12 h-12 object-cover rounded-full" />
                                                <div>
                                                    <p className={`font-semibold ${theme.textPrimary}`}>{item.name}</p>
                                                </div>
                                            </div>
                                            <input
                                                type="number"
                                                min="0"
                                                value={foodOrderData.items[item.id] || 0}
                                                onChange={(e) => handleFoodOrderChange(e, item.id)}
                                                className={`w-20 p-2 text-center rounded-lg ${theme.bgSecondary} ${theme.textPrimary} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-amber-500`}
                                            />
                                        </div>
                                    ))}
                                </div>
                                <button type="submit" className={`w-full py-3 rounded-full ${theme.buttonBg} ${theme.buttonText} font-bold shadow-lg ${theme.buttonHover} transition-colors disabled:opacity-50`} disabled={isBookingLoading}>
                                    {isBookingLoading ? 'Placing Order...' : 'Place Order'}
                                </button>
                                {bookingMessage.text && (
                                    <div className={`mt-4 p-3 rounded-xl text-center ${bookingMessage.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
                                        {bookingMessage.text}
                                    </div>
                                )}
                            </form>
                        </div>
                    </div>
                )}

                <footer data-contact-section className="bg-transparent text-white py-8 px-4 md:px-12 mt-12">
                    <div className="container mx-auto flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
                        {resortInfo && (
                            <>
                                <div className="text-center md:text-left">
                                    <h3 className="text-xl font-bold tracking-tight text-gray-800">{resortInfo.name}</h3>
                                    <p className="text-sm text-gray-700 mt-1">{resortInfo.address}</p>
                                    <p className="text-xs text-gray-600 mt-2">&copy; 2024 Elysian Retreat. All Rights Reserved.</p>
                                </div>
                                <div className="flex space-x-4 text-gray-700">
                                    <a href={formatUrl(resortInfo.facebook)} target="_blank" rel="noopener noreferrer" className="hover:text-gray-900 transition-colors"><Facebook /></a>
                                    <a href={formatUrl(resortInfo.instagram)} target="_blank" rel="noopener noreferrer" className="hover:text-gray-900 transition-colors"><Instagram /></a>
                                    <a href={formatUrl(resortInfo.twitter)} target="_blank" rel="noopener noreferrer" className="hover:text-gray-900 transition-colors"><Twitter /></a>
                                    <a href={formatUrl(resortInfo.linkedin)} target="_blank" rel="noopener noreferrer" className="hover:text-gray-900 transition-colors"><Linkedin /></a>
                                </div>
                            </>
                        )}
                    </div>
                    <div className="mt-6 pt-6 border-t border-gray-300/20 text-center">
                        <a
                            href="https://teqmates.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
                        >
                            Powered by <span className="font-semibold">TeqMates</span>
                        </a>
                    </div>
                </footer>
            </div>
        </>
    );
}