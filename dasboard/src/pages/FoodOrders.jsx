import React, { useEffect, useState, useMemo } from "react";
import { useLocation } from "react-router-dom";
import DashboardLayout from "../layout/DashboardLayout";
import api from "../services/api";
import API from "../services/api";
import { Bar, Line } from "react-chartjs-2";
import "chart.js/auto";
import { ChefHat, X, Package, Home, UtensilsCrossed, Truck } from "lucide-react";
import { toast } from "react-hot-toast";
import { getMediaBaseUrl } from "../utils/env";
import { formatDateTimeIST, formatDateIST } from "../utils/dateUtils";
import { normalizeQuantity } from "../utils/quantityValidation";

export default function FoodOrders() {
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("dashboard"); // "dashboard", "orders", "requests", or "management"

  // Set active tab based on route
  useEffect(() => {
    if (location.pathname.includes("/food-categories") || location.pathname.includes("/food-items")) {
      setActiveTab("management");
    } else if (location.pathname.includes("/food-orders")) {
      setActiveTab("dashboard");
    } else {
      setActiveTab("dashboard");
    }
  }, [location.pathname]);

  // Food Order Requests state
  const [foodOrderRequests, setFoodOrderRequests] = useState([]);
  const [assigningRequestId, setAssigningRequestId] = useState(null);
  const [selectedEmployeeForRequest, setSelectedEmployeeForRequest] = useState("");

  // Dashboard state
  const [dashboardData, setDashboardData] = useState({
    totalRevenue: 0,
    totalOrders: 0,
    completedOrders: 0,
    pendingOrders: 0,
    deliveryOrders: 0,
    dineInOrders: 0,
    totalItemsSold: 0,
    topItems: [],
    salesByDate: [],
    ordersByStatus: [],
    employeePerformance: [],
    revenueByType: [],
    itemsUsage: [],
    // Business metrics (initialized to prevent undefined errors)
    totalCOGS: 0,
    totalProfit: 0,
    profitMargin: 0,
    averageOrderValue: 0,
    averageCOGS: 0,
    averageProfit: 0,
    orderCosts: []
  });
  const [dashboardFilters, setDashboardFilters] = useState({
    fromDate: "",
    toDate: "",
    orderType: "all"
  });
  const [allOrdersForDashboard, setAllOrdersForDashboard] = useState([]);
  const [recipesData, setRecipesData] = useState({});
  const [orders, setOrders] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [foodItems, setFoodItems] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [roomId, setRoomId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [amount, setAmount] = useState(0);
  const [orderType, setOrderType] = useState("dine_in"); // "dine_in" or "room_service"
  const [deliveryRequest, setDeliveryRequest] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [hasMore, setHasMore] = useState(true);
  const [isFetchingMore, setIsFetchingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [viewingIngredients, setViewingIngredients] = useState(null);
  const [ingredientsData, setIngredientsData] = useState({});
  const [loadingIngredients, setLoadingIngredients] = useState(false);
  const [recipesCache, setRecipesCache] = useState({}); // Cache recipes by food_item_id
  const [showDeliveryRequestModal, setShowDeliveryRequestModal] = useState(null);
  const [deliveryRequestText, setDeliveryRequestText] = useState("");
  const [showCompleteModal, setShowCompleteModal] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState("unpaid");

  // Food Management states (from FoodCategory.jsx)
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState(""); // Base price for dine-in
  const [roomServicePrice, setRoomServicePrice] = useState(""); // Price for room service/parcel
  const [images, setImages] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);
  const [editingItemId, setEditingItemId] = useState(null);
  const [available, setAvailable] = useState(true);
  const [alwaysAvailable, setAlwaysAvailable] = useState(false); // Always available option
  const [filters, setFilters] = useState({ search: "", category: "all", availability: "all" });
  const [categoryName, setCategoryName] = useState("");
  const [categoryImageFile, setCategoryImageFile] = useState(null);
  const [categoryPreviewUrl, setCategoryPreviewUrl] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [editCategoryId, setEditCategoryId] = useState(null);

  // Extra inventory items for food item
  const [extraInventoryItems, setExtraInventoryItems] = useState([]);
  const [inventoryItemsList, setInventoryItemsList] = useState([]);

  // Available time for food item
  const [availableFromTime, setAvailableFromTime] = useState("");
  const [availableToTime, setAvailableToTime] = useState("");

  // Time-wise pricing
  const [timeWisePrices, setTimeWisePrices] = useState([]);

  const statusColors = {
    pending: "bg-yellow-100 text-yellow-800",
    in_progress: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    completed: "bg-green-100 text-green-800",
    cancelled: "bg-red-100 text-red-800",
    scheduled: "bg-orange-100 text-orange-800",
  };

  const token = localStorage.getItem("token");

  // Helper function for image URLs
  const getImageUrl = (imagePath) => {
    if (!imagePath) return 'https://placehold.co/400x300/e2e8f0/a0aec0?text=No+Image';
    if (imagePath.startsWith('http')) return imagePath;
    const baseUrl = getMediaBaseUrl();
    return imagePath.startsWith('/') ? `${baseUrl}${imagePath}` : `${baseUrl}/${imagePath}`;
  };

  // KPI Card component
  const KpiCard = ({ title, value, icon, color }) => (
    <div className={`p-6 rounded-2xl text-white shadow-lg flex items-center justify-between transition-transform duration-300 transform hover:scale-105 ${color}`}>
      <div>
        <h4 className="text-lg font-medium">{title}</h4>
        <p className="text-3xl font-bold mt-1">{value}</p>
      </div>
      <div className="text-4xl opacity-80">{icon}</div>
    </div>
  );

  useEffect(() => {
    fetchAll();
    if (activeTab === "management") {
      fetchCategories();
      fetchFoodItems();
      fetchInventoryItems();
    } else if (activeTab === "requests") {
      fetchFoodOrderRequests();
    } else if (activeTab === "dashboard") {
      fetchAllOrdersForDashboard();
    }
  }, [activeTab]);

  // Fetch inventory items for extra items selection
  const fetchInventoryItems = async () => {
    try {
      const res = await api.get("/inventory/items?limit=1000");
      setInventoryItemsList(res.data || []);
    } catch (error) {
      console.error("Failed to fetch inventory items:", error);
      setInventoryItemsList([]);
    }
  };

  // Handle extra inventory items
  const handleAddExtraInventoryItem = () => {
    setExtraInventoryItems([...extraInventoryItems, { inventory_item_id: "", quantity: 1 }]);
  };

  const handleUpdateExtraInventoryItem = (index, field, value) => {
    const updated = [...extraInventoryItems];
    if (field === "quantity") {
      const invItem = inventoryItemsList.find(item => item.id === parseInt(updated[index].inventory_item_id));
      updated[index][field] = normalizeQuantity(value, invItem?.unit);
    } else {
      updated[index][field] = value;
    }
    setExtraInventoryItems(updated);
  };

  const handleRemoveExtraInventoryItem = (index) => {
    setExtraInventoryItems(extraInventoryItems.filter((_, i) => i !== index));
  };

  // Handle time-wise pricing
  const handleAddTimeWisePrice = () => {
    setTimeWisePrices([...timeWisePrices, { from_time: "", to_time: "", price: "" }]);
  };

  const handleUpdateTimeWisePrice = (index, field, value) => {
    const updated = [...timeWisePrices];
    updated[index][field] = value;
    setTimeWisePrices(updated);
  };

  const handleRemoveTimeWisePrice = (index) => {
    setTimeWisePrices(timeWisePrices.filter((_, i) => i !== index));
  };

  useEffect(() => {
    if (activeTab === "dashboard") {
      calculateDashboardData();
    }
  }, [activeTab, allOrdersForDashboard, dashboardFilters, recipesData]);

  // Fetch all orders for dashboard analysis
  const fetchAllOrdersForDashboard = async () => {
    try {
      // Fetch orders, food items, employees, and inventory items in parallel
      const [ordersRes, foodItemsRes, employeesRes, inventoryRes] = await Promise.all([
        api.get("/food-orders?limit=10000").catch(err => {
          console.error("Error fetching orders:", err);
          return { data: [] };
        }),
        api.get("/food-items").catch(err => {
          console.error("Error fetching food items:", err);
          return { data: [] };
        }),
        api.get("/employees").catch(err => {
          console.error("Error fetching employees:", err);
          return { data: [] };
        }),
        api.get("/inventory/items?limit=10000").catch(err => {
          console.error("Error fetching inventory items:", err);
          return { data: [] };
        })
      ]);

      const orders = ordersRes.data || [];
      const foodItems = foodItemsRes.data || [];
      const employees = employeesRes.data || [];
      const inventoryItems = inventoryRes.data || [];

      // Create lookup maps
      const foodItemsMap = {};
      foodItems.forEach(item => {
        foodItemsMap[item.id] = item;
      });

      const employeesMap = {};
      employees.forEach(emp => {
        employeesMap[emp.id] = emp;
      });

      const inventoryItemsMap = {};
      inventoryItems.forEach(item => {
        inventoryItemsMap[item.id] = item;
      });

      // Store inventory items map for cost calculations
      setInventoryItemsList(inventoryItems);

      // Enrich orders with food item and employee details
      const enrichedOrders = orders.map(order => {
        const enrichedOrder = { ...order };

        // Enrich items with food item details
        if (enrichedOrder.items && Array.isArray(enrichedOrder.items)) {
          enrichedOrder.items = enrichedOrder.items.map(item => {
            const foodItem = foodItemsMap[item.food_item_id];
            return {
              ...item,
              food_item: foodItem || { id: item.food_item_id, name: `Item ${item.food_item_id}`, price: 0 }
            };
          });
        }

        // Enrich employee details
        if (enrichedOrder.assigned_employee_id) {
          enrichedOrder.assigned_employee = employeesMap[enrichedOrder.assigned_employee_id] || {
            id: enrichedOrder.assigned_employee_id,
            name: `Employee ${enrichedOrder.assigned_employee_id}`
          };
        }

        return enrichedOrder;
      });

      setAllOrdersForDashboard(enrichedOrders);

      // Also fetch recipes for inventory usage tracking
      fetchRecipesForInventory(foodItems);
    } catch (error) {
      console.error("Failed to fetch orders for dashboard:", error);
      setAllOrdersForDashboard([]);
    }
  };

  // Fetch recipes for inventory usage tracking
  const fetchRecipesForInventory = async (foodItems) => {
    try {
      const recipePromises = foodItems.map(item =>
        api.get(`/recipes?food_item_id=${item.id}`).catch(() => ({ data: [] }))
      );
      const recipeResponses = await Promise.all(recipePromises);

      const recipesMap = {};
      recipeResponses.forEach((res, idx) => {
        const recipes = res.data || [];
        if (recipes.length > 0) {
          recipesMap[foodItems[idx].id] = recipes[0]; // Take first recipe if multiple
        }
      });

      setRecipesData(recipesMap);
    } catch (error) {
      console.error("Failed to fetch recipes:", error);
    }
  };

  // Calculate dashboard metrics
  const calculateDashboardData = () => {
    let filteredOrders = [...allOrdersForDashboard];

    // Apply date filters
    if (dashboardFilters.fromDate) {
      filteredOrders = filteredOrders.filter(order =>
        order.created_at && order.created_at >= dashboardFilters.fromDate
      );
    }
    if (dashboardFilters.toDate) {
      filteredOrders = filteredOrders.filter(order =>
        order.created_at && order.created_at <= `${dashboardFilters.toDate}T23:59:59`
      );
    }
    if (dashboardFilters.orderType !== "all") {
      filteredOrders = filteredOrders.filter(order =>
        order.order_type === dashboardFilters.orderType
      );
    }

    // Calculate totals
    const totalRevenue = filteredOrders
      .filter(o => o.status === "completed")
      .reduce((sum, o) => sum + (parseFloat(o.amount) || 0), 0);

    const totalOrders = filteredOrders.length;
    const completedOrders = filteredOrders.filter(o => o.status === "completed").length;
    const pendingOrders = filteredOrders.filter(o => o.status === "pending").length;
    const deliveryOrders = filteredOrders.filter(o => o.order_type === "room_service").length;
    const dineInOrders = filteredOrders.filter(o => o.order_type === "dine_in").length;

    // Calculate items sold
    const itemsMap = {};
    let totalItemsSold = 0;
    filteredOrders.forEach(order => {
      if (order.items && Array.isArray(order.items)) {
        order.items.forEach(item => {
          const itemId = item.food_item_id;
          const quantity = item.quantity || 0;
          totalItemsSold += quantity;

          if (!itemsMap[itemId]) {
            itemsMap[itemId] = {
              food_item_id: itemId,
              food_item_name: item.food_item?.name || `Item ${itemId}`,
              quantity: 0,
              revenue: 0
            };
          }
          itemsMap[itemId].quantity += quantity;
          if (order.status === "completed") {
            const itemPrice = item.food_item?.price || 0;
            itemsMap[itemId].revenue += itemPrice * quantity;
          }
        });
      }
    });

    // Top items by quantity
    const topItems = Object.values(itemsMap)
      .sort((a, b) => b.quantity - a.quantity)
      .slice(0, 10);

    // Sales by date
    const salesByDateMap = {};
    filteredOrders
      .filter(o => o.status === "completed")
      .forEach(order => {
        const date = order.created_at ? order.created_at.split('T')[0] : '';
        if (date) {
          if (!salesByDateMap[date]) {
            salesByDateMap[date] = { date, revenue: 0, orders: 0 };
          }
          salesByDateMap[date].revenue += parseFloat(order.amount) || 0;
          salesByDateMap[date].orders += 1;
        }
      });
    const salesByDate = Object.values(salesByDateMap)
      .sort((a, b) => new Date(a.date) - new Date(b.date))
      .slice(-30); // Last 30 days

    // Orders by status
    const statusCounts = {};
    filteredOrders.forEach(order => {
      const status = order.status || "unknown";
      statusCounts[status] = (statusCounts[status] || 0) + 1;
    });
    const ordersByStatus = Object.entries(statusCounts).map(([status, count]) => ({
      name: status.replace("_", " ").toUpperCase(),
      value: count
    }));

    // Employee performance
    const employeeMap = {};
    filteredOrders
      .filter(o => o.status === "completed" && o.assigned_employee_id)
      .forEach(order => {
        const empId = order.assigned_employee_id;
        if (!employeeMap[empId]) {
          employeeMap[empId] = {
            employee_id: empId,
            employee_name: order.assigned_employee?.name || `Employee ${empId}`,
            orders: 0,
            revenue: 0
          };
        }
        employeeMap[empId].orders += 1;
        employeeMap[empId].revenue += parseFloat(order.amount) || 0;
      });
    const employeePerformance = Object.values(employeeMap)
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 10);

    // Revenue by type
    const revenueByType = [
      {
        name: "Dine In",
        value: filteredOrders
          .filter(o => o.order_type === "dine_in" && o.status === "completed")
          .reduce((sum, o) => sum + (parseFloat(o.amount) || 0), 0)
      },
      {
        name: "Room Service",
        value: filteredOrders
          .filter(o => o.order_type === "room_service" && o.status === "completed")
          .reduce((sum, o) => sum + (parseFloat(o.amount) || 0), 0)
      }
    ];

    // Items usage (inventory items used in food items)
    const itemsUsageMap = {};
    filteredOrders.forEach(order => {
      if (order.items && Array.isArray(order.items)) {
        order.items.forEach(item => {
          // Get recipe from recipesData map
          const foodItemId = item.food_item_id;
          const recipe = recipesData[foodItemId];

          if (recipe && recipe.ingredients && Array.isArray(recipe.ingredients)) {
            recipe.ingredients.forEach(ing => {
              const invId = ing.inventory_item_id;
              const quantity = (parseFloat(ing.quantity) || 0) * (item.quantity || 0);
              if (!itemsUsageMap[invId]) {
                itemsUsageMap[invId] = {
                  inventory_item_id: invId,
                  inventory_item_name: ing.inventory_item?.name || ing.inventory_item_name || `Item ${invId}`,
                  quantity: 0,
                  unit: ing.inventory_item?.unit || ing.unit || "unit"
                };
              }
              itemsUsageMap[invId].quantity += quantity;
            });
          }
        });
      }
    });
    const itemsUsage = Object.values(itemsUsageMap)
      .sort((a, b) => b.quantity - a.quantity)
      .slice(0, 20);

    // Calculate Cost of Goods Sold (COGS) and Profit
    const completedOrdersList = filteredOrders.filter(o => o.status === "completed");
    let totalCOGS = 0;
    let totalProfit = 0;
    const orderCosts = [];

    completedOrdersList.forEach(order => {
      let orderCOGS = 0;
      if (order.items && Array.isArray(order.items)) {
        order.items.forEach(item => {
          const foodItemId = item.food_item_id;
          const quantity = item.quantity || 0;
          const recipe = recipesData[foodItemId];

          if (recipe && recipe.ingredients && Array.isArray(recipe.ingredients)) {
            const servings = recipe.servings || 1;
            const recipeMultiplier = quantity / servings;

            recipe.ingredients.forEach(ing => {
              const invItem = inventoryItemsList.find(inv => inv.id === ing.inventory_item_id);
              if (invItem && invItem.unit_price) {
                const ingredientCost = (ing.quantity || 0) * invItem.unit_price * recipeMultiplier;
                orderCOGS += ingredientCost;
              }
            });
          }

          // Add extra inventory items cost for room service
          if (order.order_type === "room_service" && item.food_item?.extra_inventory_items) {
            item.food_item.extra_inventory_items.forEach(extra => {
              const invItem = inventoryItemsList.find(inv => inv.id === extra.inventory_item_id);
              if (invItem && invItem.unit_price) {
                orderCOGS += (extra.quantity || 0) * invItem.unit_price * quantity;
              }
            });
          }
        });
      }

      const orderRevenue = parseFloat(order.amount) || 0;
      const orderProfit = orderRevenue - orderCOGS;
      totalCOGS += orderCOGS;
      totalProfit += orderProfit;

      orderCosts.push({
        orderId: order.id,
        revenue: orderRevenue,
        cost: orderCOGS,
        profit: orderProfit,
        margin: orderRevenue > 0 ? ((orderProfit / orderRevenue) * 100) : 0
      });
    });

    const profitMargin = totalRevenue > 0 ? ((totalProfit / totalRevenue) * 100) : 0;
    const averageOrderValue = completedOrders > 0 ? totalRevenue / completedOrders : 0;
    const averageCOGS = completedOrders > 0 ? totalCOGS / completedOrders : 0;
    const averageProfit = completedOrders > 0 ? totalProfit / completedOrders : 0;

    // Calculate item costs and profits
    Object.keys(itemsMap).forEach(itemId => {
      const item = itemsMap[itemId];
      const recipe = recipesData[itemId];
      let itemCost = 0;

      if (recipe && recipe.ingredients && Array.isArray(recipe.ingredients)) {
        const servings = recipe.servings || 1;
        const recipeMultiplier = item.quantity / servings;
        recipe.ingredients.forEach(ing => {
          const invItem = inventoryItemsList.find(inv => inv.id === ing.inventory_item_id);
          if (invItem && invItem.unit_price) {
            itemCost += (ing.quantity || 0) * invItem.unit_price * recipeMultiplier;
          }
        });
      }

      item.cost = itemCost;
      item.profit = item.revenue - itemCost;
      item.margin = item.revenue > 0 ? ((item.profit / item.revenue) * 100) : 0;
    });

    setDashboardData({
      totalRevenue,
      totalOrders,
      completedOrders,
      pendingOrders,
      deliveryOrders,
      dineInOrders,
      totalItemsSold,
      topItems,
      salesByDate,
      ordersByStatus,
      employeePerformance,
      revenueByType,
      itemsUsage,
      // Business metrics
      totalCOGS,
      totalProfit,
      profitMargin,
      averageOrderValue,
      averageCOGS,
      averageProfit,
      orderCosts
    });
  };

  // Fetch food order requests (service requests with food_order_id)
  const fetchFoodOrderRequests = async () => {
    try {
      const res = await api.get("/service-requests?limit=1000");
      // Filter to only show requests with food_order_id (food order requests)
      const foodRequests = (res.data || []).filter(req => req.food_order_id);
      setFoodOrderRequests(foodRequests);
    } catch (error) {
      console.error("Failed to fetch food order requests:", error);
      setFoodOrderRequests([]);
    }
  };

  // Accept a food order request (change status to in_progress)
  const handleAcceptRequest = async (requestId) => {
    try {
      await api.put(`/service-requests/${requestId}`, {
        status: "in_progress"
      });
      toast.success("Request accepted successfully!");
      fetchFoodOrderRequests();
      fetchAll(); // Refresh orders list
    } catch (error) {
      console.error("Failed to accept request:", error);
      toast.error("Failed to accept request.");
    }
  };

  // Assign employee to a food order request
  const handleAssignEmployeeToRequest = async (requestId) => {
    if (!selectedEmployeeForRequest) {
      toast.error("Please select an employee.");
      return;
    }
    try {
      await api.put(`/service-requests/${requestId}`, {
        employee_id: parseInt(selectedEmployeeForRequest),
        status: "in_progress"
      });
      toast.success("Employee assigned successfully!");
      setAssigningRequestId(null);
      setSelectedEmployeeForRequest("");
      fetchFoodOrderRequests();
      fetchAll(); // Refresh orders list
    } catch (error) {
      console.error("Failed to assign employee:", error);
      toast.error("Failed to assign employee.");
    }
  };

  // Update request status
  const handleUpdateRequestStatus = async (requestId, newStatus) => {
    try {
      await api.put(`/service-requests/${requestId}`, {
        status: newStatus
      });
      toast.success("Request status updated successfully!");
      fetchFoodOrderRequests();
      fetchAll();
    } catch (error) {
      console.error("Failed to update request status:", error);
      toast.error("Failed to update request status.");
    }
  };

  // Delete a food order request
  const handleDeleteRequest = async (requestId) => {
    if (!window.confirm("Are you sure you want to delete this request?")) return;
    try {
      await api.delete(`/service-requests/${requestId}`);
      toast.success("Request deleted successfully!");
      fetchFoodOrderRequests();
    } catch (error) {
      console.error("Failed to delete request:", error);
      toast.error("Failed to delete request.");
    }
  };

  // Food Management functions
  const fetchCategories = async () => {
    try {
      const res = await API.get("/food-categories", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCategories(res.data);
    } catch (err) {
      console.error("Failed to load categories:", err);
    }
  };

  const fetchFoodItems = async () => {
    try {
      const res = await API.get("/food-items", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFoodItems(res.data);
    } catch (err) {
      console.error("Failed to fetch items", err);
    }
  };

  const handleFoodImageChange = (e) => {
    const newFiles = Array.from(e.target.files);
    setImages((prevImages) => [...prevImages, ...newFiles]);
    const newPreviews = newFiles.map((file) => URL.createObjectURL(file));
    setImagePreviews((prev) => [...prev, ...newPreviews]);
  };

  const handleRemoveFoodImage = (index) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
    setImagePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleFoodEdit = (item) => {
    setEditingItemId(item.id);
    setName(item.name);
    setDescription(item.description);
    setPrice(item.price || "");
    setRoomServicePrice(item.room_service_price || "");
    setSelectedCategory(item.category_id);
    setAvailable(item.available);
    setAlwaysAvailable(item.always_available || false);
    setImagePreviews(item.images?.map((img) => getImageUrl(img.image_url)) || []);
    setImages([]);
    setAvailableFromTime(item.available_from_time || "");
    setAvailableToTime(item.available_to_time || "");
    setExtraInventoryItems(item.extra_inventory_items || []);
    setTimeWisePrices(item.time_wise_prices || []);
  };

  const resetFoodForm = () => {
    setName("");
    setDescription("");
    setPrice("");
    setRoomServicePrice("");
    setSelectedCategory("");
    setImages([]);
    setImagePreviews([]);
    setEditingItemId(null);
    setAvailable(true);
    setAlwaysAvailable(false);
    setExtraInventoryItems([]);
    setAvailableFromTime("");
    setAvailableToTime("");
    setTimeWisePrices([]);
  };

  const handleFoodSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    const formData = new FormData();
    formData.append("name", name);
    formData.append("description", description);
    formData.append("price", price);
    // Add room service price if provided
    if (roomServicePrice) {
      formData.append("room_service_price", roomServicePrice);
    }
    formData.append("category_id", selectedCategory);
    formData.append("available", available);
    formData.append("always_available", alwaysAvailable);
    images.forEach((img) => formData.append("images", img));

    // Add available time (only if not always available)
    if (!alwaysAvailable) {
      if (availableFromTime) {
        formData.append("available_from_time", availableFromTime);
      }
      if (availableToTime) {
        formData.append("available_to_time", availableToTime);
      }
    }

    // Add extra inventory items (only for parcel/room service)
    // These are automatically applied to room service orders only
    if (extraInventoryItems.length > 0) {
      formData.append("extra_inventory_items", JSON.stringify(
        extraInventoryItems.map(item => ({
          inventory_item_id: parseInt(item.inventory_item_id),
          quantity: parseFloat(item.quantity) || 0,
          for_room_service: true // Mark as room service only
        }))
      ));
    }

    // Add time-wise pricing
    if (timeWisePrices.length > 0) {
      formData.append("time_wise_prices", JSON.stringify(
        timeWisePrices.map(tp => ({
          from_time: tp.from_time,
          to_time: tp.to_time,
          price: parseFloat(tp.price) || 0
        }))
      ));
    }

    try {
      if (editingItemId) {
        await API.put(`/food-items/${editingItemId}/`, formData, {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
        });
        toast.success("Food item updated successfully!");
      } else {
        await API.post("/food-items/", formData, {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
        });
        toast.success("Food item added successfully!");
      }
      fetchFoodItems();
      resetFoodForm();
    } catch (err) {
      console.error("Failed to save food item", err);
      toast.error("Failed to save food item.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleFoodDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;
    setIsLoading(true);
    try {
      await API.delete(`/food-items/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      fetchFoodItems();
      toast.success("Food item deleted successfully!");
    } catch (err) {
      console.error("Delete failed", err);
      toast.error("Failed to delete food item.");
    } finally {
      setIsLoading(false);
    }
  };

  const toggleFoodAvailability = async (item) => {
    setIsLoading(true);
    try {
      await API.patch(
        `/food-items/${item.id}/toggle-availability?available=${!item.available}`,
        null,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchFoodItems();
      toast.success(`Item status toggled to ${item.available ? 'Not Available' : 'Available'}`);
    } catch (err) {
      console.error("Failed to toggle availability", err);
      toast.error("Failed to toggle availability.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryImageChange = (e) => {
    const file = e.target.files[0];
    setCategoryImageFile(file);
    if (file) {
      setCategoryPreviewUrl(URL.createObjectURL(file));
    } else {
      setCategoryPreviewUrl(null);
    }
  };

  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    if (!categoryName) {
      toast.error("Please fill in the category name.");
      return;
    }
    setIsLoading(true);
    const formData = new FormData();
    formData.append("name", categoryName);
    if (categoryImageFile) formData.append("image", categoryImageFile);

    try {
      if (editCategoryId) {
        await API.put(`/food-categories/${editCategoryId}`, formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setEditCategoryId(null);
        toast.success("Category updated successfully!");
      } else {
        if (!categoryImageFile) {
          toast.error("Please select an image for the new category.");
          setIsLoading(false);
          return;
        }
        await API.post("/food-categories", formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        toast.success("Category added successfully!");
      }
      setCategoryName("");
      setCategoryImageFile(null);
      setCategoryPreviewUrl(null);
      fetchCategories();
    } catch (err) {
      console.error("Failed to save category:", err);
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || "Failed to save category.";
      toast.error(`Failed to save category: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryEdit = (cat) => {
    setEditCategoryId(cat.id);
    setCategoryName(cat.name);
    setCategoryPreviewUrl(getImageUrl(`uploads/food_categories/${cat.image}`));
    setCategoryImageFile(null);
  };

  const handleCategoryDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this category?")) return;
    setIsLoading(true);
    try {
      await API.delete(`/food-categories/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchCategories();
      toast.success("Category deleted successfully!");
    } catch (err) {
      console.error("Failed to delete:", err);
      toast.error("Failed to delete category. Check if it's in use.");
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAll = async () => {
    try {
      // Fetch initial page of orders, rooms, bookings, and other data
      const [ordersRes, roomsRes, employeesRes, foodItemsRes, bookingsRes, packageBookingsRes, inventoryRes] = await Promise.all([
        api.get("/food-orders?skip=0&limit=20").catch(err => {
          console.error("Error fetching food orders:", err);
          return { data: [] };
        }),
        api.get("/rooms?limit=1000").catch(err => {
          console.error("Error fetching rooms:", err);
          return { data: [] };
        }),
        api.get("/employees").catch(err => {
          console.error("Error fetching employees:", err);
          return { data: [] };
        }),
        api.get("/food-items").catch(err => {
          console.error("Error fetching food items:", err);
          return { data: [] };
        }),
        api.get("/bookings?limit=1000").catch(err => {
          console.error("Error fetching bookings:", err);
          return { data: { bookings: [] } };
        }),
        api.get("/packages/bookingsall?limit=1000").catch(err => {
          console.error("Error fetching package bookings:", err);
          return { data: [] };
        }),
        api.get("/inventory/items?limit=10000").catch(err => {
          console.error("Error fetching inventory items:", err);
          return { data: [] };
        })
      ]);
      setOrders(ordersRes?.data || []);
      setHasMore((ordersRes?.data || []).length === 20);
      console.log("Food Orders - Employees fetched:", employeesRes?.data);
      setEmployees(Array.isArray(employeesRes?.data) ? employeesRes.data : []);
      setFoodItems(foodItemsRes?.data || []);
      setInventoryItemsList(inventoryRes?.data || []);

      // Fetch recipes for profitability calculation
      if (foodItemsRes.data && foodItemsRes.data.length > 0) {
        fetchRecipesForInventory(foodItemsRes.data);
      }

      try {
        // Filter rooms to only show checked-in rooms (similar to Services page)
        const allRooms = roomsRes?.data || [];
        const regularBookings = bookingsRes?.data?.bookings || [];
        const packageBookings = (packageBookingsRes?.data || []).map(pb => ({ ...pb, is_package: true }));

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const checkedInRoomIds = new Set();

        // Helper function to normalize status
        const normalizeStatus = (status) => {
          if (!status) return '';
          return status.toLowerCase().replace(/[-_\s]/g, '');
        };

        // Helper function to check if status is checked-in or booked (active booking)
        const isActiveBooking = (status) => {
          if (!status) return false;
          const normalized = status.toLowerCase().replace(/[-_\s]/g, '');
          return (normalized === 'checkedin' || normalized === 'booked') &&
            normalized !== 'cancelled' &&
            !normalized.includes('checkedout');
        };

        // Get room IDs from active regular bookings
        regularBookings.forEach(booking => {
          if (isActiveBooking(booking.status)) {
            try {
              const checkInDate = new Date(booking.check_in);
              const checkOutDate = new Date(booking.check_out);
              checkInDate.setHours(0, 0, 0, 0);
              checkOutDate.setHours(0, 0, 0, 0);

              if (checkInDate <= today && checkOutDate >= today) {
                if (booking.rooms && Array.isArray(booking.rooms)) {
                  booking.rooms.forEach(room => {
                    if (room && room.id) checkedInRoomIds.add(room.id);
                  });
                }
              }
            } catch (e) {
              console.error("Error processing regular booking:", e);
            }
          }
        });

        // Get room IDs from active package bookings
        packageBookings.forEach(booking => {
          if (isActiveBooking(booking.status)) {
            try {
              const checkInDate = new Date(booking.check_in);
              const checkOutDate = new Date(booking.check_out);
              checkInDate.setHours(0, 0, 0, 0);
              checkOutDate.setHours(0, 0, 0, 0);

              if (checkInDate <= today && checkOutDate >= today) {
                if (booking.rooms && Array.isArray(booking.rooms)) {
                  booking.rooms.forEach(roomLink => {
                    const room = roomLink.room || roomLink;
                    const roomId = room?.id || roomLink.room_id;
                    if (roomId) checkedInRoomIds.add(roomId);
                  });
                }
              }
            } catch (e) {
              console.error("Error processing package booking:", e);
            }
          }
        });

        // Also check room status directly
        allRooms.forEach(room => {
          const roomStatusNormalized = normalizeStatus(room.status);
          if (roomStatusNormalized === 'checkedin' ||
            roomStatusNormalized === 'booked' ||
            roomStatusNormalized === 'occupied' ||
            roomStatusNormalized.includes('checkedin')) {
            checkedInRoomIds.add(room.id);
          }
        });

        const checkedInRooms = allRooms.filter(room => checkedInRoomIds.has(room.id));
        setRooms(checkedInRooms);
      } catch (roomFilterError) {
        console.error("Error during room filtering:", roomFilterError);
        setRooms([]);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
      // Only clear orders if the main call failed
      setOrders(prev => prev.length ? prev : []);
    }
  };

  const fetchOrders = async () => {
    try {
      const ordersRes = await api.get("/food-orders?skip=0&limit=20");
      setOrders(ordersRes.data || []);
      setPage(1);
      setHasMore(ordersRes.data?.length === 20);
    } catch (error) {
      console.error("Failed to fetch orders:", error);
      setOrders([]);
    }
  };

  const loadMoreOrders = async () => {
    if (isFetchingMore || !hasMore) return;
    setIsFetchingMore(true);
    const nextPage = page + 1;
    try {
      const res = await api.get(`/food-orders?skip=${(nextPage - 1) * 20}&limit=20`);
      const newOrders = res.data || [];
      setOrders(prev => [...prev, ...newOrders]);
      setPage(nextPage);
      setHasMore(newOrders.length === 20);
    } catch (err) {
      console.error("Failed to load more orders:", err);
    } finally {
      setIsFetchingMore(false);
    }
  };

  const handleAddItem = () => {
    setSelectedItems([...selectedItems, { food_item_id: "", quantity: 1 }]);
  };

  const handleItemChange = (index, field, value) => {
    const updated = [...selectedItems];
    // Food quantities are always whole numbers (pcs)
    updated[index][field] = field === "quantity" ? Math.round(parseFloat(value) || 0) : value;
    setSelectedItems(updated);
    calculateAmount(updated);
  };

  const calculateAmount = (items) => {
    let total = 0;
    items.forEach((item) => {
      const food = foodItems.find((f) => f.id === parseInt(item.food_item_id));
      if (food) total += food.price * item.quantity;
    });
    setAmount(total);
  };

  const handleSubmit = async () => {
    if (!roomId || !employeeId || selectedItems.length === 0) {
      alert("Please select room, employee, and at least one food item.");
      return;
    }

    const payload = {
      room_id: parseInt(roomId),
      billing_status: "unbilled",
      assigned_employee_id: parseInt(employeeId),
      amount,
      order_type: orderType,
      delivery_request: orderType === "room_service" && deliveryRequest ? deliveryRequest : null,
      items: selectedItems.map((item) => ({
        food_item_id: parseInt(item.food_item_id),
        quantity: item.quantity,
      })),
    };

    try {
      const res = await api.post("/food-orders/", payload);
      toast.success("Order created successfully!");

      // Manually add to state to ensure immediate visibility
      if (res.data) {
        setOrders(prev => [res.data, ...prev]);
      }

      // Only refresh orders table, not all data
      fetchOrders();
      // Also refresh dashboard data if on dashboard tab
      if (activeTab === "dashboard") {
        fetchAllOrdersForDashboard();
      }
      setSelectedItems([]);
      setRoomId("");
      setEmployeeId("");
      setAmount(0);
      setOrderType("dine_in");
      setDeliveryRequest("");

      // Clear filters to ensure visibility
      setStatusFilter("");
      setDateFilter("");

      // Auto-scroll to the orders list to show the new order
      setTimeout(() => {
        const ordersSection = document.getElementById("orders-list-section");
        if (ordersSection) {
          ordersSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    } catch (err) {
      console.error(err);
      toast.error("Failed to submit order.");
    }
  };

  const handleStatusChange = async (id, newStatus) => {
    // If completing, show modal for paid/unpaid selection
    if (newStatus === "completed") {
      const order = orders.find(o => o.id === id);
      setShowCompleteModal(order);
      setPaymentStatus(order.billing_status === "paid" ? "paid" : "unpaid");
      return;
    }


    // Optimistically update UI immediately
    setOrders(prev => prev.map(o => o.id === id ? { ...o, status: newStatus } : o));

    // For other status changes, update directly
    try {
      await api.put(`/food-orders/${id}`, { status: newStatus });
      toast.success("Order status updated successfully!");
      fetchOrders();
      // Also refresh dashboard data if on dashboard tab
      if (activeTab === "dashboard") {
        fetchAllOrdersForDashboard();
      }
    } catch (error) {
      console.error("Failed to update status:", error);
      toast.error("Failed to update order status.");
      // Revert optimistic update on error
      fetchOrders();
    }
  };

  const handleCompleteOrder = async () => {
    if (!showCompleteModal) return;

    const orderId = showCompleteModal.id;
    // Optimistic update
    setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: "completed", billing_status: paymentStatus } : o));
    setShowCompleteModal(null);
    setPaymentStatus("unpaid");

    try {
      await api.put(`/food-orders/${orderId}`, {
        status: "completed",
        billing_status: paymentStatus
      });

      toast.success("Order completed successfully!");
      fetchOrders();
      // Also refresh dashboard data if on dashboard tab
      if (activeTab === "dashboard") {
        fetchAllOrdersForDashboard();
      }
    } catch (error) {
      console.error("Failed to complete order:", error);
      toast.error("Failed to complete order.");
      fetchOrders(); // Revert optimistic update
    }
  };

  const handleRaiseDeliveryRequest = (order) => {
    setShowDeliveryRequestModal(order.id);
    setDeliveryRequestText(order.delivery_request || "");
  };

  const handleSubmitDeliveryRequest = async (orderId) => {
    try {
      await api.put(`/food-orders/${orderId}`, {
        delivery_request: deliveryRequestText
      });
      setShowDeliveryRequestModal(null);
      setDeliveryRequestText("");
      toast.success("Delivery request updated successfully!");
      fetchOrders();
    } catch (error) {
      console.error("Failed to update delivery request:", error);
      toast.error("Failed to update delivery request.");
    }
  };

  // Fetch recipes for a food item (with caching)
  const fetchRecipeForFoodItem = async (foodItemId) => {
    // Check cache first
    if (recipesCache[foodItemId]) {
      return recipesCache[foodItemId];
    }

    try {
      const response = await api.get(`/recipes?food_item_id=${foodItemId}`);
      const recipes = response.data || [];
      // Cache the result
      setRecipesCache(prev => ({ ...prev, [foodItemId]: recipes }));
      return recipes;
    } catch (error) {
      console.error(`Failed to fetch recipe for food item ${foodItemId}:`, error);
      return [];
    }
  };

  // Calculate aggregated ingredients for an order
  const calculateOrderIngredients = async (order) => {
    setLoadingIngredients(true);
    try {
      const ingredientMap = new Map(); // inventory_item_id -> { name, code, totalQuantity, unit, notes }

      // Fetch recipes for all food items in the order
      const recipePromises = order.items.map(item =>
        fetchRecipeForFoodItem(item.food_item_id)
      );
      const recipeArrays = await Promise.all(recipePromises);

      // Process each item and its recipes
      order.items.forEach((item, itemIndex) => {
        const recipes = recipeArrays[itemIndex];
        const itemQuantity = item.quantity || 1;

        // Use the first recipe found for this food item
        if (recipes && recipes.length > 0) {
          const recipe = recipes[0]; // Use first recipe
          const servings = recipe.servings || 1;

          // Calculate multiplier: how many times to multiply the recipe
          const recipeMultiplier = itemQuantity / servings;

          // Aggregate ingredients
          recipe.ingredients?.forEach(ingredient => {
            const invId = ingredient.inventory_item_id;
            const totalQty = (ingredient.quantity || 0) * recipeMultiplier;

            if (ingredientMap.has(invId)) {
              const existing = ingredientMap.get(invId);
              existing.totalQuantity += totalQty;
            } else {
              ingredientMap.set(invId, {
                name: ingredient.inventory_item_name || 'Unknown',
                code: ingredient.inventory_item_code || '',
                totalQuantity: totalQty,
                unit: ingredient.unit || 'pcs',
                notes: ingredient.notes || ''
              });
            }
          });
        }
      });

      // Convert map to array and sort by name
      const aggregatedIngredients = Array.from(ingredientMap.values())
        .sort((a, b) => a.name.localeCompare(b.name));

      setIngredientsData(prev => ({
        ...prev,
        [order.id]: aggregatedIngredients
      }));

      return aggregatedIngredients;
    } catch (error) {
      console.error("Failed to calculate ingredients:", error);
      return [];
    } finally {
      setLoadingIngredients(false);
    }
  };

  // Handle view ingredients button click
  const handleViewIngredients = async (order) => {
    setViewingIngredients(order.id);

    // If already calculated, use cached data
    if (ingredientsData[order.id]) {
      return;
    }

    // Otherwise calculate
    await calculateOrderIngredients(order);
  };

  // KPI Calculations
  const totalOrders = orders.length;
  const totalRevenue = orders.reduce((sum, o) => sum + o.amount, 0);
  const completedOrders = orders.filter((o) => o.status === "completed").length;

  // Chart Data
  const dailyOrdersData = {
    labels: Array.from({ length: 7 }, (_, i) => `Day ${i + 1}`),
    datasets: [
      {
        label: "Orders",
        data: Array.from({ length: 7 }, () => Math.floor(Math.random() * 10 + 1)),
        backgroundColor: "#4f46e5",
      },
    ],
  };

  const revenueTrendData = {
    labels: ["Week 1", "Week 2", "Week 3", "Week 4"],
    datasets: [
      {
        label: "Revenue (₹)",
        data: Array.from({ length: 4 }, () => Math.floor(Math.random() * 5000 + 2000)),
        borderColor: "#16a34a",
        backgroundColor: "rgba(22,163,74,0.2)",
        tension: 0.3,
      },
    ],
  };

  const chartOptionsSmall = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { enabled: true } },
    scales: {
      x: { grid: { display: false }, ticks: { font: { size: 10 } } },
      y: { grid: { display: false }, ticks: { font: { size: 10 } } },
    },
  };

  const filteredOrders = orders.filter((order) => {
    const matchStatus = statusFilter ? order.status === statusFilter : true;
    const matchDate = dateFilter ? order.created_at?.startsWith(dateFilter) : true;
    return matchStatus && matchDate;
  }).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  // Food Management calculations
  const totalItems = foodItems.length;
  const totalCategories = categories.length;
  const availableItemsCount = foodItems.filter(item => item.available).length;
  const filteredFoodItems = foodItems.filter(item => {
    const searchMatch = item.name.toLowerCase().includes(filters.search.toLowerCase());
    const categoryMatch = filters.category === 'all' || item.category_id === parseInt(filters.category);
    const availabilityMatch = filters.availability === 'all' ||
      (filters.availability === 'available' && item.available) ||
      (filters.availability === 'unavailable' && !item.available);
    return searchMatch && categoryMatch && availabilityMatch;
  });

  return (
    <DashboardLayout>
      <div className="p-6 space-y-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-3xl font-extrabold text-indigo-700">🍽 Food & Beverage Management</h2>
        </div>




        {/* Tabs Navigation */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 mb-6">
          <div className="flex border-b border-gray-200">
            {[
              { id: "dashboard", label: "Dashboard" },
              { id: "orders", label: "Food Orders" },
              { id: "requests", label: "Requested Orders" },
              { id: "management", label: "Food Management" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-3 font-medium transition-colors ${activeTab === tab.id
                  ? "text-indigo-600 border-b-2 border-indigo-600"
                  : "text-gray-600 hover:text-gray-900"
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Filters</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">From Date</label>
                  <input
                    type="date"
                    value={dashboardFilters.fromDate}
                    onChange={(e) => setDashboardFilters({ ...dashboardFilters, fromDate: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">To Date</label>
                  <input
                    type="date"
                    value={dashboardFilters.toDate}
                    onChange={(e) => setDashboardFilters({ ...dashboardFilters, toDate: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Order Type</label>
                  <select
                    value={dashboardFilters.orderType}
                    onChange={(e) => setDashboardFilters({ ...dashboardFilters, orderType: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="all">All Types</option>
                    <option value="dine_in">Dine In</option>
                    <option value="room_service">Room Service</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <button
                    onClick={() => setDashboardFilters({ fromDate: "", toDate: "", orderType: "all" })}
                    className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition-colors"
                  >
                    Clear Filters
                  </button>
                </div>
              </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-r from-green-500 to-green-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Total Revenue</p>
                    <p className="text-3xl font-bold mt-1">₹{(dashboardData.totalRevenue || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</p>
                  </div>
                  <div className="text-4xl opacity-80">💰</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-blue-500 to-blue-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Total Orders</p>
                    <p className="text-3xl font-bold mt-1">{dashboardData.totalOrders}</p>
                  </div>
                  <div className="text-4xl opacity-80">📦</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-purple-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Completed Orders</p>
                    <p className="text-3xl font-bold mt-1">{dashboardData.completedOrders}</p>
                    <p className="text-xs opacity-75 mt-1">
                      {dashboardData.totalOrders > 0
                        ? ((dashboardData.completedOrders / dashboardData.totalOrders) * 100).toFixed(1)
                        : 0}% completion rate
                    </p>
                  </div>
                  <div className="text-4xl opacity-80">✅</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-orange-500 to-orange-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Items Sold</p>
                    <p className="text-3xl font-bold mt-1">{dashboardData.totalItemsSold}</p>
                  </div>
                  <div className="text-4xl opacity-80">🍽️</div>
                </div>
              </div>
            </div>

            {/* Business Performance KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-r from-emerald-500 to-emerald-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Total Profit</p>
                    <p className="text-3xl font-bold mt-1">₹{(dashboardData.totalProfit || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</p>
                    <p className="text-xs opacity-75 mt-1">
                      {(dashboardData.profitMargin || 0).toFixed(1)}% margin
                    </p>
                  </div>
                  <div className="text-4xl opacity-80">💵</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-red-500 to-red-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Total COGS</p>
                    <p className="text-3xl font-bold mt-1">₹{(dashboardData.totalCOGS || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</p>
                    <p className="text-xs opacity-75 mt-1">
                      Cost of goods sold
                    </p>
                  </div>
                  <div className="text-4xl opacity-80">📊</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-teal-500 to-teal-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Avg Order Value</p>
                    <p className="text-3xl font-bold mt-1">₹{(dashboardData.averageOrderValue || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</p>
                    <p className="text-xs opacity-75 mt-1">
                      Per completed order
                    </p>
                  </div>
                  <div className="text-4xl opacity-80">📈</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-amber-500 to-amber-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Avg Profit</p>
                    <p className="text-3xl font-bold mt-1">₹{(dashboardData.averageProfit || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}</p>
                    <p className="text-xs opacity-75 mt-1">
                      Per order
                    </p>
                  </div>
                  <div className="text-4xl opacity-80">🎯</div>
                </div>
              </div>
            </div>

            {/* Secondary KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Pending Orders</p>
                    <p className="text-2xl font-bold text-yellow-600 mt-1">{dashboardData.pendingOrders}</p>
                  </div>
                  <div className="text-3xl">⏳</div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Dine In Orders</p>
                    <p className="text-2xl font-bold text-blue-600 mt-1">{dashboardData.dineInOrders}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {dashboardData.totalOrders > 0
                        ? ((dashboardData.dineInOrders / dashboardData.totalOrders) * 100).toFixed(1)
                        : 0}% of total
                    </p>
                  </div>
                  <div className="text-3xl">🍴</div>
                </div>
              </div>
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Room Service</p>
                    <p className="text-2xl font-bold text-indigo-600 mt-1">{dashboardData.deliveryOrders}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {dashboardData.totalOrders > 0
                        ? ((dashboardData.deliveryOrders / dashboardData.totalOrders) * 100).toFixed(1)
                        : 0}% of total
                    </p>
                  </div>
                  <div className="text-3xl">🚚</div>
                </div>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Sales Trend Chart */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Sales Trend</h3>
                <div className="h-64">
                  <Line
                    data={{
                      labels: dashboardData.salesByDate.map(d => new Date(d.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })),
                      datasets: [
                        {
                          label: 'Revenue (₹)',
                          data: dashboardData.salesByDate.map(d => d.revenue),
                          borderColor: 'rgb(99, 102, 241)',
                          backgroundColor: 'rgba(99, 102, 241, 0.1)',
                          tension: 0.4
                        },
                        {
                          label: 'Orders',
                          data: dashboardData.salesByDate.map(d => d.orders),
                          borderColor: 'rgb(16, 185, 129)',
                          backgroundColor: 'rgba(16, 185, 129, 0.1)',
                          tension: 0.4,
                          yAxisID: 'y1'
                        }
                      ]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: true },
                        tooltip: { mode: 'index', intersect: false }
                      },
                      scales: {
                        y: {
                          type: 'linear',
                          display: true,
                          position: 'left',
                          title: { display: true, text: 'Revenue (₹)' }
                        },
                        y1: {
                          type: 'linear',
                          display: true,
                          position: 'right',
                          title: { display: true, text: 'Orders' },
                          grid: { drawOnChartArea: false }
                        }
                      }
                    }}
                  />
                </div>
              </div>

              {/* Order Status Distribution */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Order Status Distribution</h3>
                <div className="h-64">
                  <Bar
                    data={{
                      labels: dashboardData.ordersByStatus.map(s => s.name),
                      datasets: [{
                        label: 'Orders',
                        data: dashboardData.ordersByStatus.map(s => s.value),
                        backgroundColor: [
                          'rgba(234, 179, 8, 0.8)',
                          'rgba(59, 130, 246, 0.8)',
                          'rgba(16, 185, 129, 0.8)',
                          'rgba(239, 68, 68, 0.8)'
                        ]
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: { stepSize: 1 }
                        }
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Revenue by Type and Top Items */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Revenue by Type */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Revenue by Order Type</h3>
                <div className="h-64">
                  <Bar
                    data={{
                      labels: dashboardData.revenueByType.map(t => t.name),
                      datasets: [{
                        label: 'Revenue (₹)',
                        data: dashboardData.revenueByType.map(t => t.value),
                        backgroundColor: [
                          'rgba(59, 130, 246, 0.8)',
                          'rgba(139, 92, 246, 0.8)'
                        ]
                      }]
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false },
                        tooltip: {
                          callbacks: {
                            label: function (context) {
                              return '₹' + context.parsed.y.toLocaleString('en-IN');
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: {
                            callback: function (value) {
                              return '₹' + value.toLocaleString('en-IN');
                            }
                          }
                        }
                      }
                    }}
                  />
                </div>
                <div className="mt-4 space-y-2">
                  {dashboardData.revenueByType.map((type, idx) => (
                    <div key={idx} className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">{type.name}</span>
                      <span className="font-semibold text-gray-800">
                        ₹{type.value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Top Selling Items with Profitability */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Top 10 Selling Items (Profitability)</h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {dashboardData.topItems.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No data available</p>
                  ) : (
                    dashboardData.topItems.map((item, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-bold text-sm">
                              {idx + 1}
                            </div>
                            <div>
                              <p className="font-medium text-gray-800">{item.food_item_name}</p>
                              <p className="text-xs text-gray-500">Qty: {item.quantity}</p>
                            </div>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                          <div>
                            <p className="text-gray-500">Revenue</p>
                            <p className="font-semibold text-green-600">
                              ₹{item.revenue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-500">Cost</p>
                            <p className="font-semibold text-red-600">
                              ₹{((item.cost || 0)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-500">Profit</p>
                            <p className={`font-semibold ${(item.profit || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                              ₹{((item.profit || 0)).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                            </p>
                            <p className="text-gray-400 text-xs">
                              {(item.margin || 0).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Employee Performance and Items Usage */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Employee Performance */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Top Employee Performance</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Employee</th>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Orders</th>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Revenue</th>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Avg/Order</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {dashboardData.employeePerformance.length === 0 ? (
                        <tr>
                          <td colSpan="4" className="py-4 text-center text-gray-500">No data available</td>
                        </tr>
                      ) : (
                        dashboardData.employeePerformance.map((emp, idx) => (
                          <tr key={idx} className="hover:bg-gray-50">
                            <td className="py-2 px-4 text-sm font-medium">{emp.employee_name}</td>
                            <td className="py-2 px-4 text-sm">{emp.orders}</td>
                            <td className="py-2 px-4 text-sm font-semibold text-green-600">
                              ₹{emp.revenue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </td>
                            <td className="py-2 px-4 text-sm text-gray-600">
                              ₹{((emp.revenue / emp.orders) || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Items Usage with Cost */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Top Inventory Items Used (Cost Analysis)</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Item</th>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Quantity</th>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Unit</th>
                        <th className="py-2 px-4 text-left text-sm font-semibold text-gray-700">Total Cost</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {dashboardData.itemsUsage.length === 0 ? (
                        <tr>
                          <td colSpan="4" className="py-4 text-center text-gray-500">No data available</td>
                        </tr>
                      ) : (
                        dashboardData.itemsUsage.map((item, idx) => {
                          const invItem = inventoryItemsList.find(inv => inv.id === item.inventory_item_id);
                          const itemCost = (item.quantity || 0) * (invItem?.unit_price || 0);
                          return (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="py-2 px-4 text-sm font-medium">{item.inventory_item_name}</td>
                              <td className="py-2 px-4 text-sm">{item.quantity.toFixed(2)}</td>
                              <td className="py-2 px-4 text-sm text-gray-500">{item.unit}</td>
                              <td className="py-2 px-4 text-sm font-semibold text-red-600">
                                ₹{itemCost.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Profitability Analysis */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-800 mb-4">Profitability Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Profit Margin</p>
                  <p className="text-3xl font-bold text-green-600">{dashboardData.profitMargin.toFixed(1)}%</p>
                  <p className="text-xs text-gray-500 mt-1">Overall margin</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Revenue to Cost Ratio</p>
                  <p className="text-3xl font-bold text-blue-600">
                    {dashboardData.totalCOGS > 0
                      ? (dashboardData.totalRevenue / dashboardData.totalCOGS).toFixed(2)
                      : '0.00'}x
                  </p>
                  <p className="text-xs text-gray-500 mt-1">For every ₹1 cost</p>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">Avg Cost per Order</p>
                  <p className="text-3xl font-bold text-purple-600">
                    ₹{(dashboardData.averageCOGS || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Average COGS</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Food Orders Tab */}
        {activeTab === "orders" && (
          <div className="space-y-6">
            {/* Overview Section */}
            <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl p-6 border border-indigo-100">
              <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                Order Overview
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Total Orders</p>
                  <p className="text-2xl font-bold text-indigo-600">{totalOrders}</p>
                </div>
                <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Total Revenue</p>
                  <p className="text-2xl font-bold text-green-600">₹{totalRevenue.toLocaleString('en-IN')}</p>
                </div>
                <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Completed</p>
                  <p className="text-2xl font-bold text-blue-600">{completedOrders}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {totalOrders > 0 ? ((completedOrders / totalOrders) * 100).toFixed(0) : 0}% rate
                  </p>
                </div>
                <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Pending</p>
                  <p className="text-2xl font-bold text-orange-600">{totalOrders - completedOrders}</p>
                  <p className="text-xs text-gray-400 mt-1">Needs attention</p>
                </div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-lg p-5 text-white shadow-md">
                <p className="text-sm font-medium opacity-90 mb-1">Average Order Value</p>
                <p className="text-2xl font-bold">
                  ₹{totalOrders > 0 ? (totalRevenue / totalOrders).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : '0'}
                </p>
                <p className="text-xs opacity-75 mt-1">Per order</p>
              </div>
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-5 text-white shadow-md">
                <p className="text-sm font-medium opacity-90 mb-1">Items per Order</p>
                <p className="text-2xl font-bold">
                  {(() => {
                    const totalItems = orders.reduce((sum, o) => sum + (o.items?.length || 0), 0);
                    return totalOrders > 0 ? (totalItems / totalOrders).toFixed(1) : '0.0';
                  })()}
                </p>
                <p className="text-xs opacity-75 mt-1">Average items</p>
              </div>
              <div className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-lg p-5 text-white shadow-md">
                <p className="text-sm font-medium opacity-90 mb-1">Fulfillment Rate</p>
                <p className="text-2xl font-bold">
                  {totalOrders > 0 ? ((completedOrders / totalOrders) * 100).toFixed(0) : 0}%
                </p>
                <p className="text-xs opacity-75 mt-1">Completion rate</p>
              </div>
              <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg p-5 text-white shadow-md">
                <p className="text-sm font-medium opacity-90 mb-1">Revenue/Hour</p>
                <p className="text-2xl font-bold">
                  ₹{(() => {
                    const hours = Math.max(1, Math.floor((new Date() - new Date(orders[0]?.created_at || Date.now())) / (1000 * 60 * 60)));
                    return (totalRevenue / hours).toLocaleString('en-IN', { maximumFractionDigits: 0 });
                  })()}
                </p>
                <p className="text-xs opacity-75 mt-1">Hourly average</p>
              </div>
            </div>

            {/* Create New Order Section */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
              <div className="mb-6">
                <h3 className="text-xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                  <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                  Create New Food Order
                </h3>
                <p className="text-sm text-gray-500">Quickly create orders for checked-in guests</p>
              </div>

              <div className="space-y-5">
                {/* Room and Employee Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Select Room *</label>
                    <select
                      value={roomId}
                      onChange={(e) => setRoomId(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-black"
                    >
                      <option value="">Choose a room...</option>
                      {rooms.length === 0 ? (
                        <option disabled>No checked-in rooms available</option>
                      ) : (
                        rooms.map((room) => (
                          <option key={room.id} value={room.id}>
                            Room {room.number || room.room_number || room.id}
                          </option>
                        ))
                      )}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Assign Employee * {employees.length > 0 && <span className="text-xs text-gray-400">({employees.length} found)</span>}
                    </label>
                    <select
                      value={employeeId}
                      onChange={(e) => setEmployeeId(e.target.value)}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition text-black font-medium"
                    >
                      <option value="">{employees.length === 0 ? "Searching for employees..." : "Choose an employee..."}</option>
                      {Array.isArray(employees) && [...employees]
                        .filter(emp => emp && emp.id)
                        .sort((a, b) => {
                          const aOnline = a.status === 'on_duty' || a.is_clocked_in;
                          const bOnline = b.status === 'on_duty' || b.is_clocked_in;
                          if (aOnline && !bOnline) return -1;
                          if (!aOnline && bOnline) return 1;
                          return 0;
                        })
                        .map((emp) => {
                          const isOnline = emp.status === 'on_duty' || emp.is_clocked_in;
                          return (
                            <option
                              key={emp.id}
                              value={emp.id}
                              style={{ color: isOnline ? "#16a34a" : "inherit", fontWeight: isOnline ? "bold" : "normal" }}
                            >
                              {emp.name || `Employee ${emp.id}`} {isOnline ? " 🟢 (Online)" : `(${emp.status || 'off_duty'})`}
                            </option>
                          );
                        })}
                    </select>
                  </div>
                </div>

                {/* Order Type Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">Order Type *</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        setOrderType("dine_in");
                        setDeliveryRequest("");
                      }}
                      className={`flex items-center justify-center gap-2 p-4 border-2 rounded-lg transition-all ${orderType === "dine_in"
                        ? "border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm"
                        : "border-gray-300 hover:border-indigo-300 text-gray-700 bg-white"
                        }`}
                    >
                      <UtensilsCrossed size={20} />
                      <span className="font-semibold">Dine In</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setOrderType("room_service")}
                      className={`flex items-center justify-center gap-2 p-4 border-2 rounded-lg transition-all ${orderType === "room_service"
                        ? "border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm"
                        : "border-gray-300 hover:border-indigo-300 text-gray-700 bg-white"
                        }`}
                    >
                      <Home size={20} />
                      <span className="font-semibold">Room Service</span>
                    </button>
                  </div>
                </div>

                {/* Delivery Request (only for room service) */}
                {orderType === "room_service" && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                      <Truck size={16} />
                      Delivery Instructions (Optional)
                    </label>
                    <textarea
                      placeholder="Add delivery instructions, timing preferences, or special notes..."
                      className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition resize-none"
                      rows="3"
                      value={deliveryRequest}
                      onChange={(e) => setDeliveryRequest(e.target.value)}
                    />
                  </div>
                )}

                {/* Food Items Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">Food Items *</label>
                  <div className="space-y-3">
                    {selectedItems.map((item, index) => (
                      <div key={index} className="flex gap-3 items-center bg-gray-50 p-3 rounded-lg">
                        <select
                          value={item.food_item_id}
                          onChange={(e) => handleItemChange(index, "food_item_id", e.target.value)}
                          className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-black"
                        >
                          <option value="">Select food item...</option>
                          {foodItems.map((f) => (
                            <option key={f.id} value={f.id}>
                              {f.name} - ₹{f.price}
                            </option>
                          ))}
                        </select>
                        <input
                          type="number"
                          min={1}
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, "quantity", e.target.value)}
                          placeholder="Qty"
                          className="w-20 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-center"
                        />
                      </div>
                    ))}
                    <button
                      onClick={handleAddItem}
                      type="button"
                      className="w-full bg-indigo-100 hover:bg-indigo-200 text-indigo-700 font-medium rounded-lg px-4 py-2.5 transition-colors border border-indigo-300"
                    >
                      + Add Food Item
                    </button>
                  </div>
                </div>

                {/* Total and Submit */}
                <div className="pt-4 border-t border-gray-200">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-lg font-semibold text-gray-700">Order Total:</span>
                    <span className="text-2xl font-bold text-indigo-600">₹{amount.toLocaleString('en-IN')}</span>
                  </div>
                  <button
                    onClick={handleSubmit}
                    disabled={!roomId || !employeeId || selectedItems.length === 0}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg shadow-md hover:shadow-lg transition-all"
                  >
                    Create Order
                  </button>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-5">
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Status</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-black"
                  >
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                    <option value="scheduled">Scheduled</option>
                  </select>
                </div>
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Date</label>
                  <input
                    type="date"
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  />
                </div>
                {(statusFilter || dateFilter) && (
                  <div className="flex items-end">
                    <button
                      onClick={() => {
                        setStatusFilter("");
                        setDateFilter("");
                      }}
                      className="px-4 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
                    >
                      Clear Filters
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Orders List */}
            <div id="orders-list-section">
              <div className="mb-4">
                <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                  <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                  All Orders ({filteredOrders.length})
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredOrders.length === 0 ? (
                  <div className="col-span-full text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                    <p className="text-gray-500">No orders found</p>
                    <p className="text-sm text-gray-400 mt-1">Try adjusting your filters</p>
                  </div>
                ) : (
                  filteredOrders.map((order) => {
                    const roomData = rooms.find((r) => r.id === order.room_id);
                    // Normalize 'active' status to 'pending' for UI display
                    const normalizedStatus = order.status === 'active' ? 'pending' : order.status;
                    return (
                      <div
                        key={order.id}
                        className="bg-white rounded-lg shadow-md border border-gray-200 p-5 hover:shadow-lg transition-all"
                      >
                        {/* Header */}
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h4 className="font-bold text-lg text-gray-800">
                              Room {roomData?.number || roomData?.room_number || order.room_number || order.room_id}
                            </h4>
                            <p className="text-xs text-gray-500 mt-1">
                              {order.created_at ? formatDateTimeIST(order.created_at) : 'N/A'}
                            </p>
                          </div>
                          <div className="flex flex-col gap-2 items-end">
                            <span
                              className={`px-2.5 py-1 rounded-full text-xs font-semibold ${order.order_type === "room_service"
                                ? "bg-purple-100 text-purple-700"
                                : "bg-blue-100 text-blue-700"
                                }`}
                            >
                              {order.order_type === "room_service" ? "Room Service" : "Dine In"}
                            </span>
                            <span
                              className={`px-2.5 py-1 rounded-full text-xs font-semibold ${statusColors[normalizedStatus] || "bg-gray-100 text-gray-800"
                                }`}
                            >
                              {normalizedStatus.replace("_", " ")}
                            </span>
                          </div>
                        </div>

                        {/* Order Details */}
                        <div className="space-y-2 mb-3 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-500">Guest:</span>
                            <span className="font-medium text-gray-800">{order.guest_name || "N/A"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-500">Employee:</span>
                            <span className="font-medium text-gray-800">
                              {order.employee_name || employees.find((e) => e.id === order.assigned_employee_id)?.name || "N/A"}
                            </span>
                          </div>
                        </div>
                        {/* Delivery Request */}
                        {order.order_type === "room_service" && order.delivery_request && (
                          <div className="mb-3 p-2 bg-purple-50 border border-purple-200 rounded-lg">
                            <div className="flex items-start gap-2">
                              <Truck size={14} className="text-purple-600 mt-0.5 flex-shrink-0" />
                              <div className="flex-1">
                                <p className="text-xs font-semibold text-purple-700 mb-1">Delivery Instructions:</p>
                                <p className="text-xs text-purple-600">{order.delivery_request}</p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Scheduled Order Info */}
                        {/* Scheduled Order Info */}
                        {normalizedStatus === "scheduled" && order.delivery_request && order.delivery_request.includes("SCHEDULED_FOR:") && (
                          <div className="mb-4 p-3 bg-amber-50 border-l-4 border-amber-500 rounded-r-lg shadow-sm">
                            <div className="flex items-center gap-3">
                              <div className="bg-amber-100 p-2 rounded-full">
                                <span className="text-xl" role="img" aria-label="clock">⏰</span>
                              </div>
                              <div className="flex-1">
                                <p className="text-xs font-bold text-amber-600 uppercase tracking-wider mb-0.5">Scheduled Delivery</p>
                                <p className="text-lg font-extrabold text-gray-800 font-mono">
                                  {order.delivery_request.split("--")[0].replace("SCHEDULED_FOR:", "").trim()}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Order Items */}
                        <div className="mb-3">
                          <p className="text-xs font-semibold text-gray-700 mb-1">Items ({order.items?.length || 0}):</p>
                          <ul className="space-y-1">
                            {order.items?.slice(0, 3).map((item, i) => (
                              <li key={i} className="text-xs text-gray-600 flex justify-between">
                                <span>{item.food_item_name}</span>
                                <span className="font-medium">×{item.quantity}</span>
                              </li>
                            ))}
                            {order.items?.length > 3 && (
                              <li className="text-xs text-gray-400 italic">+{order.items.length - 3} more items</li>
                            )}
                          </ul>
                        </div>

                        {/* Amount */}
                        <div className="mb-3 p-2 bg-gray-50 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">Order Total:</span>
                            <span className="text-lg font-bold text-indigo-600">₹{parseFloat(order.amount || 0).toLocaleString('en-IN')}</span>
                          </div>
                        </div>
                        {/* Cost and Profit (Estimated Cost for all orders) */}
                        {(() => {
                          let orderCost = 0;
                          order.items?.forEach(item => {
                            const recipe = recipesCache[item.food_item_id]?.[0] || recipesData[item.food_item_id];
                            if (recipe && recipe.ingredients) {
                              const servings = recipe.servings || 1;
                              const multiplier = (item.quantity || 0) / servings;
                              recipe.ingredients.forEach(ing => {
                                const invItem = inventoryItemsList.find(inv => inv.id === ing.inventory_item_id);
                                if (invItem && invItem.unit_price) {
                                  orderCost += (ing.quantity || 0) * invItem.unit_price * multiplier;
                                }
                              });
                            }
                            if (order.order_type === "room_service" && item.food_item?.extra_inventory_items) {
                              item.food_item.extra_inventory_items.forEach(extra => {
                                const invItem = inventoryItemsList.find(inv => inv.id === extra.inventory_item_id);
                                if (invItem && invItem.unit_price) {
                                  orderCost += (extra.quantity || 0) * invItem.unit_price * (item.quantity || 0);
                                }
                              });
                            }
                          });

                          if (orderCost > 0) {
                            return (
                              <div className="mt-2 text-xs text-gray-500 bg-gray-50 p-2 rounded border border-gray-100 flex justify-between">
                                <span className="font-medium">Recipe Cost (Est):</span>
                                <span className="font-bold text-gray-700">₹{orderCost.toFixed(2)}</span>
                              </div>
                            );
                          }
                          return null;
                        })()}


                        {/* Actions */}
                        <div className="space-y-2">
                          <button
                            onClick={() => handleViewIngredients(order)}
                            className="w-full bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-sm font-medium px-3 py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
                          >
                            <ChefHat size={16} />
                            View Ingredients
                          </button>
                          <select
                            value={normalizedStatus}
                            onChange={(e) => handleStatusChange(order.id, e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm text-black focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
                          >
                            <option value="pending">Pending</option>
                            <option value="in_progress">In Progress</option>
                            <option value="completed">Completed</option>
                            <option value="cancelled">Cancelled</option>
                          </select>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Load More Orders Button */}
            {hasMore && (
              <div className="text-center mt-6">
                <button
                  onClick={loadMoreOrders}
                  disabled={isFetchingMore}
                  className="bg-indigo-100 text-indigo-700 font-semibold px-6 py-2 rounded-lg hover:bg-indigo-200 transition-colors disabled:bg-gray-200 disabled:text-gray-500"
                >
                  {isFetchingMore ? "Loading..." : "Load More Orders"}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Ingredients View Modal */}
        {viewingIngredients && (() => {
          const order = orders.find(o => o.id === viewingIngredients);
          const ingredients = ingredientsData[viewingIngredients] || [];
          const roomData = rooms.find((r) => r.id === order?.room_id);

          return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="bg-indigo-600 text-white p-6 flex justify-between items-center">
                  <div>
                    <h3 className="text-2xl font-bold flex items-center gap-2">
                      <ChefHat size={24} />
                      Order Ingredients
                    </h3>
                    <p className="text-indigo-100 mt-1">
                      Room: {roomData?.number || roomData?.room_number || order?.room_id} |
                      Order #{order?.id} |
                      {order?.items?.length || 0} item(s)
                    </p>
                  </div>
                  <button
                    onClick={() => setViewingIngredients(null)}
                    className="text-white hover:text-gray-200 transition-colors"
                  >
                    <X size={24} />
                  </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto flex-1">
                  {loadingIngredients ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                      <p className="mt-4 text-gray-600">Calculating ingredients...</p>
                    </div>
                  ) : ingredients.length === 0 ? (
                    <div className="text-center py-8">
                      <Package size={48} className="mx-auto text-gray-400 mb-4" />
                      <p className="text-gray-600">No recipes found for the items in this order.</p>
                      <p className="text-sm text-gray-500 mt-2">
                        Please add recipes for the food items in the Inventory → Recipe section.
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Order Items Summary */}
                      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                        <h4 className="font-semibold text-gray-700 mb-2">Order Items:</h4>
                        <ul className="space-y-1">
                          {order?.items?.map((item, i) => (
                            <li key={i} className="text-sm text-gray-600">
                              • {item.food_item_name} × {item.quantity}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Aggregated Ingredients */}
                      <div className="mb-4">
                        <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                          <Package size={20} />
                          Required Ingredients (Total):
                        </h4>
                        <div className="space-y-2">
                          {ingredients.map((ing, index) => (
                            <div
                              key={index}
                              className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
                            >
                              <div className="flex-1">
                                <div className="font-medium text-gray-800">
                                  {ing.name}
                                  {ing.code && (
                                    <span className="text-xs text-gray-500 ml-2">({ing.code})</span>
                                  )}
                                </div>
                                {ing.notes && (
                                  <div className="text-xs text-gray-600 mt-1">{ing.notes}</div>
                                )}
                              </div>
                              <div className="text-right">
                                <div className="font-bold text-indigo-700">
                                  {ing.totalQuantity.toFixed(2)} {ing.unit}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Summary Stats */}
                      <div className="mt-6 p-4 bg-indigo-50 rounded-lg">
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">Total Ingredients:</span>
                            <span className="font-semibold ml-2">{ingredients.length}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">Total Quantity:</span>
                            <span className="font-semibold ml-2">
                              {ingredients.reduce((sum, ing) => sum + ing.totalQuantity, 0).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Footer */}
                <div className="bg-gray-50 p-4 flex justify-end">
                  <button
                    onClick={() => setViewingIngredients(null)}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2 rounded-lg transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          );
        })()}

        {/* Delivery Request Modal */}
        {showDeliveryRequestModal && (() => {
          const order = orders.find(o => o.id === showDeliveryRequestModal);
          const roomData = rooms.find((r) => r.id === order?.room_id);
          return (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
              <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                {/* Header */}
                <div className="bg-purple-600 text-white p-6 flex justify-between items-center">
                  <div>
                    <h3 className="text-2xl font-bold flex items-center gap-2">
                      <Truck size={24} />
                      Delivery Request
                    </h3>
                    <p className="text-purple-100 mt-1">
                      Room: {roomData?.number || roomData?.room_number || order?.room_id} |
                      Order #{order?.id} | Room Service
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setShowDeliveryRequestModal(null);
                      setDeliveryRequestText("");
                    }}
                    className="text-white hover:text-gray-200 transition-colors"
                  >
                    <X size={24} />
                  </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto flex-1">
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Delivery Instructions / Special Requests
                      </label>
                      <textarea
                        placeholder="Enter delivery instructions, timing preferences, special requests, or any notes for the room service delivery..."
                        className="w-full border rounded-xl px-4 py-3 focus:ring-2 focus:ring-purple-500 transition resize-none"
                        rows="6"
                        value={deliveryRequestText}
                        onChange={(e) => setDeliveryRequestText(e.target.value)}
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Add any special delivery instructions, timing preferences, or notes for the room service order.
                      </p>
                    </div>

                    {order?.delivery_request && (
                      <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <p className="text-xs font-semibold text-gray-600 mb-1">Current Request:</p>
                        <p className="text-sm text-gray-700">{order.delivery_request}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer */}
                <div className="bg-gray-50 p-4 flex justify-end gap-3">
                  <button
                    onClick={() => {
                      setShowDeliveryRequestModal(null);
                      setDeliveryRequestText("");
                    }}
                    className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold px-6 py-2 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleSubmitDeliveryRequest(showDeliveryRequestModal)}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2 rounded-lg transition-colors"
                  >
                    {order?.delivery_request ? "Update Request" : "Submit Request"}
                  </button>
                </div>
              </div>
            </div>
          );
        })()}

        {/* Complete Order Modal */}
        {showCompleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full">
              <div className="bg-indigo-600 text-white p-6 rounded-t-2xl">
                <h3 className="text-xl font-bold">Complete Food Order</h3>
                <p className="text-indigo-100 mt-1">
                  Order #{showCompleteModal.id} | Room: {rooms.find(r => r.id === showCompleteModal.room_id)?.number || showCompleteModal.room_id}
                </p>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Payment Status *
                  </label>
                  {parseFloat(showCompleteModal.amount || 0) > 0 ? (
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setPaymentStatus("paid")}
                        className={`p-3 border-2 rounded-xl transition-all ${paymentStatus === "paid"
                          ? "border-green-500 bg-green-50 text-green-700"
                          : "border-gray-300 hover:border-green-300 text-gray-700"
                          }`}
                      >
                        <span className="font-semibold">Paid</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setPaymentStatus("unpaid")}
                        className={`p-3 border-2 rounded-xl transition-all ${paymentStatus === "unpaid"
                          ? "border-red-500 bg-red-50 text-red-700"
                          : "border-gray-300 hover:border-red-300 text-gray-700"
                          }`}
                      >
                        <span className="font-semibold">Unpaid</span>
                      </button>
                    </div>
                  ) : (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-xl text-center">
                      <span className="font-semibold text-green-700">Complimentary / Package Included</span>
                      <p className="text-xs text-green-600 mt-1">No payment required.</p>
                    </div>
                  )}
                </div>
                {showCompleteModal.order_type === "room_service" && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <p className="text-sm text-purple-700">
                      <strong>Note:</strong> A delivery service request will be automatically created for this room service order.
                    </p>
                  </div>
                )}
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={() => {
                      setShowCompleteModal(null);
                      setPaymentStatus("unpaid");
                    }}
                    className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold px-4 py-2 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCompleteOrder}
                    className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
                  >
                    Complete Order
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Requested Orders Tab */}
        {activeTab === "requests" && (
          <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-sm font-medium text-gray-600 mb-2">Total Requests</h3>
                <p className="text-3xl font-bold text-indigo-600">{foodOrderRequests.length}</p>
              </div>
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-sm font-medium text-gray-600 mb-2">Pending</h3>
                <p className="text-3xl font-bold text-yellow-600">
                  {foodOrderRequests.filter(r => r.status === "pending").length}
                </p>
              </div>
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-sm font-medium text-gray-600 mb-2">In Progress</h3>
                <p className="text-3xl font-bold text-blue-600">
                  {foodOrderRequests.filter(r => r.status === "in_progress").length}
                </p>
              </div>
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-sm font-medium text-gray-600 mb-2">Completed</h3>
                <p className="text-3xl font-bold text-green-600">
                  {foodOrderRequests.filter(r => r.status === "completed").length}
                </p>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              <div className="bg-gradient-to-r from-emerald-500 to-emerald-700 rounded-xl shadow-lg p-6 text-white">
                <h3 className="text-sm font-medium opacity-90 mb-2">Avg Fulfillment Time</h3>
                <p className="text-2xl font-bold">
                  {(() => {
                    const completed = foodOrderRequests.filter(r => r.status === "completed" && r.created_at && r.completed_at);
                    if (completed.length === 0) return "N/A";
                    const avgTime = completed.reduce((sum, r) => {
                      const created = new Date(r.created_at);
                      const completed = new Date(r.completed_at);
                      return sum + (completed - created);
                    }, 0) / completed.length;
                    const minutes = Math.floor(avgTime / (1000 * 60));
                    return minutes < 60 ? `${minutes}m` : `${Math.floor(minutes / 60)}h ${minutes % 60}m`;
                  })()}
                </p>
                <p className="text-xs opacity-75 mt-1">Time to complete</p>
              </div>
              <div className="bg-gradient-to-r from-blue-500 to-blue-700 rounded-xl shadow-lg p-6 text-white">
                <h3 className="text-sm font-medium opacity-90 mb-2">Completion Rate</h3>
                <p className="text-2xl font-bold">
                  {foodOrderRequests.length > 0
                    ? ((foodOrderRequests.filter(r => r.status === "completed").length / foodOrderRequests.length) * 100).toFixed(1)
                    : 0}%
                </p>
                <p className="text-xs opacity-75 mt-1">Requests completed</p>
              </div>
              <div className="bg-gradient-to-r from-purple-500 to-purple-700 rounded-xl shadow-lg p-6 text-white">
                <h3 className="text-sm font-medium opacity-90 mb-2">Assigned Rate</h3>
                <p className="text-2xl font-bold">
                  {foodOrderRequests.length > 0
                    ? ((foodOrderRequests.filter(r => r.employee_id).length / foodOrderRequests.length) * 100).toFixed(1)
                    : 0}%
                </p>
                <p className="text-xs opacity-75 mt-1">With assigned employee</p>
              </div>
            </div>

            {/* Requests Table */}
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="p-6 border-b border-gray-200">
                <h2 className="text-2xl font-bold text-gray-800">Food Order Requests</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">ID</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Room</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Food Order</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Request Type</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Description</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Employee</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Status</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Created At</th>
                      <th className="py-3 px-4 text-left text-sm font-semibold text-gray-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {foodOrderRequests.length === 0 ? (
                      <tr>
                        <td colSpan="9" className="py-8 text-center text-gray-500">
                          No food order requests found
                        </td>
                      </tr>
                    ) : (
                      foodOrderRequests.map((request) => (
                        <tr key={request.id} className="hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm">{request.id}</td>
                          <td className="py-3 px-4 text-sm">
                            {request.room?.number || request.room_number || "N/A"}
                          </td>
                          <td className="py-3 px-4 text-sm">
                            {request.food_order ? (
                              <div>
                                <div className="font-medium">Order #{request.food_order.id}</div>
                                <div className="text-gray-500 text-xs">
                                  ₹{request.food_order.amount || request.food_order_amount || "0"}
                                </div>
                              </div>
                            ) : (
                              "N/A"
                            )}
                          </td>
                          <td className="py-3 px-4 text-sm capitalize">{request.request_type || "delivery"}</td>
                          <td className="py-3 px-4 text-sm max-w-xs truncate">
                            {request.description || "No description"}
                          </td>
                          <td className="py-3 px-4 text-sm">
                            {request.employee?.name || request.employee_name || (
                              <span className="text-gray-400">Unassigned</span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-medium ${request.status === "pending"
                                ? "bg-yellow-100 text-yellow-800"
                                : request.status === "in_progress"
                                  ? "bg-blue-100 text-blue-800"
                                  : request.status === "completed"
                                    ? "bg-green-100 text-green-800"
                                    : "bg-red-100 text-red-800"
                                }`}
                            >
                              {request.status?.replace("_", " ").toUpperCase() || "PENDING"}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {request.created_at
                              ? new Date(request.created_at).toLocaleString()
                              : "N/A"}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex gap-2">
                              {request.status === "pending" && (
                                <>
                                  <button
                                    onClick={() => handleAcceptRequest(request.id)}
                                    className="bg-green-500 hover:bg-green-600 text-white text-xs py-1 px-3 rounded transition-colors"
                                  >
                                    Accept
                                  </button>
                                  <button
                                    onClick={() => setAssigningRequestId(request.id)}
                                    className="bg-blue-500 hover:bg-blue-600 text-white text-xs py-1 px-3 rounded transition-colors"
                                  >
                                    Assign
                                  </button>
                                </>
                              )}
                              {request.status === "in_progress" && (
                                <button
                                  onClick={() => handleUpdateRequestStatus(request.id, "completed")}
                                  className="bg-purple-500 hover:bg-purple-600 text-white text-xs py-1 px-3 rounded transition-colors"
                                >
                                  Complete
                                </button>
                              )}
                              {!request.employee_id && request.status !== "pending" && (
                                <button
                                  onClick={() => setAssigningRequestId(request.id)}
                                  className="bg-indigo-500 hover:bg-indigo-600 text-white text-xs py-1 px-3 rounded transition-colors"
                                >
                                  Assign Employee
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteRequest(request.id)}
                                className="bg-red-500 hover:bg-red-600 text-white text-xs py-1 px-3 rounded transition-colors"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Assign Employee Modal */}
            {assigningRequestId && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full mx-4">
                  <h3 className="text-xl font-bold text-gray-800 mb-4">Assign Employee</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Select Employee
                      </label>
                      <select
                        value={selectedEmployeeForRequest}
                        onChange={(e) => setSelectedEmployeeForRequest(e.target.value)}
                        className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 text-black font-medium"
                      >
                        <option value="">Choose an employee...</option>
                        {[...employees]
                          .sort((a, b) => {
                            const aOnline = a.status === 'on_duty' || a.is_clocked_in;
                            const bOnline = b.status === 'on_duty' || b.is_clocked_in;
                            if (aOnline && !bOnline) return -1;
                            if (!aOnline && bOnline) return 1;
                            return 0;
                          })
                          .map((emp) => {
                            const isOnline = emp.status === 'on_duty' || emp.is_clocked_in;
                            return (
                              <option
                                key={emp.id}
                                value={emp.id}
                                style={{ color: isOnline ? "#16a34a" : "inherit", fontWeight: isOnline ? "bold" : "normal" }}
                              >
                                {emp.name} {isOnline ? " 🟢 (Online)" : `(${emp.status || 'off_duty'})`}
                              </option>
                            );
                          })}
                      </select>
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => {
                          setAssigningRequestId(null);
                          setSelectedEmployeeForRequest("");
                        }}
                        className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleAssignEmployeeToRequest(assigningRequestId)}
                        className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                      >
                        Assign
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Food Management Tab */}
        {activeTab === "management" && (
          <div className="space-y-6">
            {error && <div className="p-4 mb-4 text-center text-red-700 bg-red-100 border border-red-200 rounded-lg">{error}</div>}

            {/* KPI Section */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              <KpiCard title="Total Food Items" value={totalItems} color="bg-gradient-to-r from-green-500 to-green-700" icon={<i className="fas fa-utensils"></i>} />
              <KpiCard title="Item Categories" value={totalCategories} color="bg-gradient-to-r from-blue-500 to-blue-700" icon={<i className="fas fa-tags"></i>} />
              <KpiCard title="Items Available" value={availableItemsCount} color="bg-gradient-to-r from-purple-500 to-purple-700" icon={<i className="fas fa-check-circle"></i>} />
            </div>

            {/* Business Performance KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gradient-to-r from-emerald-500 to-emerald-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Avg Item Price</p>
                    <p className="text-3xl font-bold mt-1">
                      ₹{totalItems > 0
                        ? (foodItems.reduce((sum, item) => sum + (parseFloat(item.price) || 0), 0) / totalItems).toLocaleString('en-IN', { maximumFractionDigits: 2 })
                        : '0.00'}
                    </p>
                  </div>
                  <div className="text-4xl opacity-80">💰</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-orange-500 to-orange-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Items with Recipes</p>
                    <p className="text-3xl font-bold mt-1">
                      {Object.keys(recipesData).length}
                    </p>
                    <p className="text-xs opacity-75 mt-1">
                      {totalItems > 0 ? ((Object.keys(recipesData).length / totalItems) * 100).toFixed(1) : 0}% coverage
                    </p>
                  </div>
                  <div className="text-4xl opacity-80">📋</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-pink-500 to-pink-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Time-based Pricing</p>
                    <p className="text-3xl font-bold mt-1">
                      {foodItems.filter(item => item.time_wise_prices && item.time_wise_prices.length > 0).length}
                    </p>
                    <p className="text-xs opacity-75 mt-1">Items with time pricing</p>
                  </div>
                  <div className="text-4xl opacity-80">⏰</div>
                </div>
              </div>
              <div className="bg-gradient-to-r from-cyan-500 to-cyan-700 rounded-xl shadow-lg p-6 text-white">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm font-medium opacity-90">Room Service Items</p>
                    <p className="text-3xl font-bold mt-1">
                      {foodItems.filter(item => item.room_service_price).length}
                    </p>
                    <p className="text-xs opacity-75 mt-1">With room service pricing</p>
                  </div>
                  <div className="text-4xl opacity-80">🚚</div>
                </div>
              </div>
            </div>

            {/* Food Item Management Section */}
            <div className="bg-white p-6 rounded-xl shadow-lg">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-800 mb-2">🍽️ Food Item Management</h2>
                <p className="text-sm text-gray-500">Create and manage food items for your menu</p>
              </div>

              <form onSubmit={handleFoodSubmit} className="space-y-6">
                {/* Basic Information Section */}
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                    Basic Information
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Item Name *</label>
                      <input
                        type="text"
                        placeholder="Enter food item name"
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Category *</label>
                      <select
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        required
                      >
                        <option value="">Select a category</option>
                        {categories.map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-2">Description *</label>
                      <textarea
                        placeholder="Describe the food item..."
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition resize-none"
                        rows="3"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        required
                      />
                    </div>
                  </div>
                </div>

                {/* Pricing Section */}
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                    Pricing
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Dine In Price (₹) *
                      </label>
                      <input
                        type="number"
                        placeholder="0.00"
                        step="0.01"
                        min="0"
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                        value={price}
                        onChange={(e) => setPrice(e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Room Service / Parcel Price (₹)
                        <span className="text-xs text-gray-500 ml-1">(Optional)</span>
                      </label>
                      <input
                        type="number"
                        placeholder="0.00"
                        step="0.01"
                        min="0"
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                        value={roomServicePrice}
                        onChange={(e) => setRoomServicePrice(e.target.value)}
                      />
                    </div>
                  </div>
                </div>

                {/* Availability Section */}
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                    Availability Settings
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-3 p-3 bg-white rounded-lg border border-gray-200">
                      <input
                        type="checkbox"
                        id="available"
                        checked={available}
                        onChange={(e) => setAvailable(e.target.checked)}
                        className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                      <label htmlFor="available" className="text-sm font-medium text-gray-700 cursor-pointer">
                        Make this item available for ordering
                      </label>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <input
                        type="checkbox"
                        id="alwaysAvailable"
                        checked={alwaysAvailable}
                        onChange={(e) => {
                          setAlwaysAvailable(e.target.checked);
                          if (e.target.checked) {
                            setAvailableFromTime("");
                            setAvailableToTime("");
                          }
                        }}
                        className="w-5 h-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                      />
                      <label htmlFor="alwaysAvailable" className="text-sm font-medium text-gray-700 cursor-pointer">
                        Always Available (24/7)
                      </label>
                      <span className="text-xs text-gray-500 ml-auto">Available at all times</span>
                    </div>
                    {!alwaysAvailable && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Available From</label>
                          <input
                            type="time"
                            value={availableFromTime}
                            onChange={(e) => setAvailableFromTime(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">Available Until</label>
                          <input
                            type="time"
                            value={availableToTime}
                            onChange={(e) => setAvailableToTime(e.target.value)}
                            className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Images Section */}
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
                    <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                    Images
                    <span className="text-xs font-normal text-gray-500 ml-2">(Optional)</span>
                  </h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Upload Images</label>
                    <input
                      type="file"
                      multiple
                      accept="image/*"
                      onChange={handleFoodImageChange}
                      className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                    />
                    {imagePreviews.length > 0 && (
                      <div className="grid grid-cols-4 gap-3 mt-4">
                        {imagePreviews.map((preview, idx) => (
                          <div key={idx} className="relative group">
                            <img src={preview} alt={`Preview ${idx + 1}`} className="w-full h-24 object-cover rounded-lg border-2 border-gray-200" />
                            <button
                              type="button"
                              onClick={() => handleRemoveFoodImage(idx)}
                              className="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Extra Inventory Items Section */}
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                        Extra Items for Room Service/Parcel
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">Add packaging, condiments, or other items (only for room service/parcel orders)</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddExtraInventoryItem}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      <span>+</span> Add Item
                    </button>
                  </div>
                  {extraInventoryItems.length === 0 ? (
                    <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-gray-300">
                      <p className="text-sm text-gray-500">No extra items added</p>
                      <p className="text-xs text-gray-400 mt-1">Click "Add Item" to add packaging or condiments</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {extraInventoryItems.map((item, idx) => (
                        <div key={idx} className="bg-white p-4 rounded-lg border border-gray-200 flex items-center gap-3">
                          <select
                            value={item.inventory_item_id}
                            onChange={(e) => handleUpdateExtraInventoryItem(idx, "inventory_item_id", e.target.value)}
                            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          >
                            <option value="">Select inventory item</option>
                            {inventoryItemsList.map((inv) => (
                              <option key={inv.id} value={inv.id}>
                                {inv.name} ({inv.unit})
                              </option>
                            ))}
                          </select>
                          <input
                            type="number"
                            placeholder="Qty"
                            value={item.quantity}
                            onChange={(e) => handleUpdateExtraInventoryItem(idx, "quantity", e.target.value)}
                            className="w-24 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                            min="0"
                            step="0.01"
                          />
                          <button
                            type="button"
                            onClick={() => handleRemoveExtraInventoryItem(idx)}
                            className="bg-red-100 hover:bg-red-200 text-red-700 px-3 py-2 rounded-lg text-sm transition-colors"
                          >
                            Remove
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Time-wise Pricing Section */}
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <span className="w-1 h-6 bg-indigo-600 rounded"></span>
                        Time-based Pricing
                        <span className="text-xs font-normal text-gray-500 ml-2">(Optional)</span>
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">Set different prices for breakfast, lunch, dinner, etc.</p>
                    </div>
                    <button
                      type="button"
                      onClick={handleAddTimeWisePrice}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                    >
                      <span>+</span> Add Price
                    </button>
                  </div>
                  {timeWisePrices.length === 0 ? (
                    <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-gray-300">
                      <p className="text-sm text-gray-500">No time-based pricing set</p>
                      <p className="text-xs text-gray-400 mt-1">Base price will be used for all times</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {timeWisePrices.map((tp, idx) => (
                        <div key={idx} className="bg-white p-4 rounded-lg border border-gray-200 grid grid-cols-12 gap-3 items-center">
                          <div className="col-span-3">
                            <label className="block text-xs text-gray-500 mb-1">From</label>
                            <input
                              type="time"
                              value={tp.from_time}
                              onChange={(e) => handleUpdateTimeWisePrice(idx, "from_time", e.target.value)}
                              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              required
                            />
                          </div>
                          <div className="col-span-3">
                            <label className="block text-xs text-gray-500 mb-1">To</label>
                            <input
                              type="time"
                              value={tp.to_time}
                              onChange={(e) => handleUpdateTimeWisePrice(idx, "to_time", e.target.value)}
                              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              required
                            />
                          </div>
                          <div className="col-span-4">
                            <label className="block text-xs text-gray-500 mb-1">Price (₹)</label>
                            <input
                              type="number"
                              placeholder="0.00"
                              value={tp.price}
                              onChange={(e) => handleUpdateTimeWisePrice(idx, "price", e.target.value)}
                              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              min="0"
                              step="0.01"
                              required
                            />
                          </div>
                          <div className="col-span-2">
                            <button
                              type="button"
                              onClick={() => handleRemoveTimeWisePrice(idx)}
                              className="w-full bg-red-100 hover:bg-red-200 text-red-700 px-3 py-2 rounded-lg text-sm transition-colors mt-6"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Submit Buttons */}
                <div className="flex gap-3 pt-4 border-t border-gray-200">
                  <button
                    type="submit"
                    className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors shadow-md hover:shadow-lg"
                  >
                    {editingItemId ? "Update Food Item" : "Create Food Item"}
                  </button>
                  {editingItemId && (
                    <button
                      type="button"
                      onClick={resetFoodForm}
                      className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-3 px-6 rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </form>

              {/* Food Items List */}
              <div className="mt-8">
                <div className="mb-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">All Food Items</h3>
                  <div className="flex flex-wrap gap-3">
                    <div className="flex-1 min-w-[200px]">
                      <input
                        type="text"
                        placeholder="🔍 Search items..."
                        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
                        value={filters.search}
                        onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                      />
                    </div>
                    <select
                      className="border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition min-w-[150px]"
                      value={filters.category}
                      onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                    >
                      <option value="all">All Categories</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name}
                        </option>
                      ))}
                    </select>
                    <select
                      className="border border-gray-300 rounded-lg px-4 py-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition min-w-[150px]"
                      value={filters.availability}
                      onChange={(e) => setFilters({ ...filters, availability: e.target.value })}
                    >
                      <option value="all">All Status</option>
                      <option value="available">Available</option>
                      <option value="unavailable">Unavailable</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredFoodItems.length === 0 ? (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                      <p className="text-gray-500">No food items found</p>
                      <p className="text-sm text-gray-400 mt-1">Try adjusting your filters</p>
                    </div>
                  ) : (
                    filteredFoodItems.map((item) => (
                      <div key={item.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                        {/* Item Image */}
                        {item.images && item.images.length > 0 && (
                          <div className="relative h-40 bg-gray-100">
                            <img
                              src={getImageUrl(item.images[0].image_url)}
                              alt={item.name}
                              className="w-full h-full object-cover"
                            />
                            <span className={`absolute top-2 right-2 px-2 py-1 rounded-full text-xs font-medium ${item.available ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                              }`}>
                              {item.available ? 'Available' : 'Unavailable'}
                            </span>
                          </div>
                        )}

                        {/* Item Details */}
                        <div className="p-4">
                          <h3 className="font-semibold text-lg text-gray-800 mb-1">{item.name}</h3>
                          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{item.description}</p>

                          {/* Pricing */}
                          <div className="mb-3 space-y-2">
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-gray-500">Dine In:</span>
                              <span className="font-semibold text-indigo-600">₹{item.price || 0}</span>
                            </div>
                            {item.room_service_price && (
                              <div className="flex justify-between items-center">
                                <span className="text-sm text-gray-500">Room Service:</span>
                                <span className="font-semibold text-purple-600">₹{item.room_service_price}</span>
                              </div>
                            )}
                          </div>

                          {/* Cost & Profit (if recipe exists) */}
                          {(() => {
                            const recipe = recipesData[item.id];
                            let itemCost = 0;
                            if (recipe && recipe.ingredients && Array.isArray(recipe.ingredients)) {
                              const servings = recipe.servings || 1;
                              recipe.ingredients.forEach(ing => {
                                const invItem = inventoryItemsList.find(inv => inv.id === ing.inventory_item_id);
                                if (invItem && invItem.unit_price) {
                                  itemCost += (ing.quantity || 0) * invItem.unit_price / servings;
                                }
                              });
                            }
                            const itemProfit = parseFloat(item.price || 0) - itemCost;
                            const margin = parseFloat(item.price || 0) > 0 ? ((itemProfit / parseFloat(item.price || 0)) * 100) : 0;
                            return itemCost > 0 ? (
                              <div className="mb-3 p-2 bg-gray-50 rounded border border-gray-200">
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                  <div className="text-center">
                                    <p className="text-gray-500 mb-1">Cost</p>
                                    <p className="font-semibold text-red-600">₹{itemCost.toFixed(0)}</p>
                                  </div>
                                  <div className="text-center">
                                    <p className="text-gray-500 mb-1">Profit</p>
                                    <p className={`font-semibold ${itemProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                      ₹{itemProfit.toFixed(0)}
                                    </p>
                                  </div>
                                  <div className="text-center">
                                    <p className="text-gray-500 mb-1">Margin</p>
                                    <p className={`font-semibold ${margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                      {margin.toFixed(0)}%
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ) : null;
                          })()}

                          {/* Actions */}
                          <div className="flex gap-2 mt-4">
                            <button
                              onClick={() => handleFoodEdit(item)}
                              className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm py-2 px-3 rounded-lg transition-colors font-medium"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => toggleFoodAvailability(item)}
                              className="bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm py-2 px-3 rounded-lg transition-colors font-medium"
                            >
                              {item.available ? 'Hide' : 'Show'}
                            </button>
                            <button
                              onClick={() => handleFoodDelete(item.id)}
                              className="bg-red-100 hover:bg-red-200 text-red-700 text-sm py-2 px-3 rounded-lg transition-colors font-medium"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Food Category Management Section */}
            <div className="bg-white p-8 rounded-2xl shadow-lg">
              <h2 className="text-2xl font-bold mb-6 text-gray-800">📁 Category Management</h2>
              <form onSubmit={handleCategorySubmit} className="mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <input
                    type="text"
                    placeholder="Category Name"
                    className="border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500"
                    value={categoryName}
                    onChange={(e) => setCategoryName(e.target.value)}
                    required
                  />
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleCategoryImageChange}
                    className="border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500"
                    required={!editCategoryId}
                  />
                  <div className="flex gap-2">
                    <button
                      type="submit"
                      className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-6 rounded-xl"
                    >
                      {editCategoryId ? "Update Category" : "Add Category"}
                    </button>
                    {editCategoryId && (
                      <button
                        type="button"
                        onClick={() => {
                          setEditCategoryId(null);
                          setCategoryName("");
                          setCategoryImageFile(null);
                          setCategoryPreviewUrl(null);
                        }}
                        className="bg-gray-500 hover:bg-gray-600 text-white font-semibold py-3 px-6 rounded-xl"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
                {categoryPreviewUrl && (
                  <img src={categoryPreviewUrl} alt="Preview" className="mt-4 w-32 h-32 object-cover rounded border" />
                )}
              </form>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {categories.map((cat) => (
                  <div key={cat.id} className="border border-gray-200 rounded-lg p-4 text-center hover:shadow-lg transition-shadow">
                    <img src={getImageUrl(`uploads/food_categories/${cat.image}`)} alt={cat.name} className="w-full h-24 object-cover rounded mb-2" />
                    <h3 className="font-semibold mb-2">{cat.name}</h3>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleCategoryEdit(cat)}
                        className="flex-1 bg-blue-500 hover:bg-blue-600 text-white text-xs py-1 px-2 rounded"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleCategoryDelete(cat.id)}
                        className="flex-1 bg-red-500 hover:bg-red-600 text-white text-xs py-1 px-2 rounded"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
