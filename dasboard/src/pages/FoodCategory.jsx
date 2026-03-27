import React, { useEffect, useState } from "react";
import DashboardLayout from "../layout/DashboardLayout";
import API from "../services/api";
import { toast } from "react-hot-toast";
import { motion } from "framer-motion";

import { getImageUrl } from "../utils/imageUtils";

// Utility moved to utils/imageUtils.js

// KPI Card for quick stats
const KpiCard = ({ title, value, icon, color }) => (
  <div className={`p-6 rounded-2xl text-white shadow-lg flex items-center justify-between transition-transform duration-300 transform hover:scale-105 ${color}`}>
    <div>
      <h4 className="text-lg font-medium">{title}</h4>
      <p className="text-3xl font-bold mt-1">{value}</p>
    </div>
    <div className="text-4xl opacity-80">{icon}</div>
  </div>
);

const FoodManagement = () => {
  // === State for UI/UX enhancements ===
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  // === State for Food Items ===
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [images, setImages] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);
  const [foodItems, setFoodItems] = useState([]);
  const [editingItemId, setEditingItemId] = useState(null);
  const [available, setAvailable] = useState(true);
  const [filters, setFilters] = useState({ search: "", category: "all", availability: "all" });

  // === State for Food Categories ===
  const [categoryName, setCategoryName] = useState("");
  const [categoryImageFile, setCategoryImageFile] = useState(null);
  const [categoryPreviewUrl, setCategoryPreviewUrl] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [editCategoryId, setEditCategoryId] = useState(null);

  const token = localStorage.getItem("token");

  // === Data Fetching Functions ===
  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await fetchCategories();
      await fetchFoodItems();
    } catch (err) {
      setError("Failed to load data. Please try again later.");
      toast.error("Failed to load data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await API.get("/food-categories", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCategories(res.data);
    } catch (err) {
      console.error("Failed to load categories:", err);
      throw err;
    }
  };

  const fetchFoodItems = async () => {
    try {
      const res = await API.get("/food-items/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFoodItems(res.data);
    } catch (err) {
      console.error("Failed to fetch items", err);
      throw err;
    }
  };

  // === Food Item Handlers ===
  const handleImageChange = (e) => {
    const newFiles = Array.from(e.target.files);
    setImages((prevImages) => [...prevImages, ...newFiles]);
    const newPreviews = newFiles.map((file) => URL.createObjectURL(file));
    setImagePreviews((prev) => [...prev, ...newPreviews]);
  };

  const handleRemoveImage = (index) => {
    setImages((prev) => prev.filter((_, i) => i !== index));
    setImagePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleEdit = (item) => {
    setEditingItemId(item.id);
    setName(item.name);
    setDescription(item.description);
    setPrice(item.price);
    setSelectedCategory(item.category_id);
    setAvailable(item.available);
    setImagePreviews(item.images?.map((img) => getImageUrl(img.image_url)) || []);
    setImages([]);
  };

  const resetForm = () => {
    setName("");
    setDescription("");
    setPrice("");
    setSelectedCategory("");
    setImages([]);
    setImagePreviews([]);
    setEditingItemId(null);
    setAvailable(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isLoading) return;
    setIsLoading(true);
    const formData = new FormData();
    formData.append("name", name);
    formData.append("description", description);
    formData.append("price", price);
    formData.append("category_id", selectedCategory);
    formData.append("available", available);
    images.forEach((img) => formData.append("images", img));

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
      resetForm();
    } catch (err) {
      console.error("Failed to save food item", err);
      toast.error("Failed to save food item.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id) => {
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

  const toggleAvailability = async (item) => {
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

  // === Food Category Handlers ===
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
    if (isLoading) return;
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
    setCategoryPreviewUrl(getImageUrl(`static/food_categories/${cat.image}`));
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

  // Derived State & Calculations
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

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex justify-center items-center h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-t-2 border-b-2 border-indigo-500"></div>
          <p className="ml-4 text-gray-600">Loading...</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6 space-y-12">
        <h1 className="text-3xl font-bold text-gray-800">Food & Beverage Management</h1>
        {error && <div className="p-4 mb-4 text-center text-red-700 bg-red-100 border border-red-200 rounded-lg">{error}</div>}

        {/* KPI Section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <KpiCard title="Total Food Items" value={totalItems} color="bg-gradient-to-r from-green-500 to-green-700" icon={<i className="fas fa-utensils"></i>} />
          <KpiCard title="Item Categories" value={totalCategories} color="bg-gradient-to-r from-blue-500 to-blue-700" icon={<i className="fas fa-tags"></i>} />
          <KpiCard title="Items Available" value={availableItemsCount} color="bg-gradient-to-r from-purple-500 to-purple-700" icon={<i className="fas fa-check-circle"></i>} />
        </div>

        {/* ====================================================== */}
        {/* Food Item Management Section */}
        {/* ====================================================== */}
        <div className="bg-white p-8 rounded-2xl shadow-lg">
          <h2 className="text-2xl font-bold mb-6 text-gray-800">🍽️ Food Item Management</h2>
          <form
            onSubmit={handleSubmit}
            className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start"
          >
            {/* Form Fields */}
            <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
              <h2 className="md:col-span-2 text-xl font-semibold text-gray-700">
                {editingItemId ? "Edit Food Item" : "Add New Food Item"}
              </h2>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Name"
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 transition duration-200"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
                <textarea
                  placeholder="Description"
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 transition duration-200"
                  rows="3"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                />
                <input
                  type="number"
                  placeholder="Price (₹)"
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 transition duration-200"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  required
                />
                <select
                  className="w-full border border-gray-300 rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 transition duration-200"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  required
                >
                  <option value="">Select Category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>
                      {cat.name}
                    </option>
                  ))}
                </select>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="form-checkbox h-5 w-5 text-indigo-600 rounded"
                    checked={available}
                    onChange={() => setAvailable(!available)}
                  />
                  <span className="text-gray-700">Available for Order</span>
                </label>
              </div>
            </div>

            {/* Image Upload and Preview */}
            <div className="w-full">
              <label className="block text-gray-700 font-medium mb-2">Upload Images</label>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              <div className="grid grid-cols-3 gap-4 mt-4">
                {imagePreviews.map((src, index) => (
                  <div key={index} className="relative group w-full aspect-square">
                    <img
                      src={src}
                      alt={`Preview ${index}`}
                      className="w-full h-full object-cover rounded-xl shadow border border-gray-200"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemoveImage(index)}
                      className="absolute top-1 right-1 bg-red-600 text-white rounded-full p-1 text-xs opacity-0 group-hover:opacity-100 transition duration-200"
                    >
                      <i className="fas fa-times"></i>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="lg:col-span-3 flex flex-col md:flex-row gap-4">
              <button
                className={`w-full text-white font-bold py-3 mt-8 rounded-xl shadow-lg transform transition-all duration-300 ${isLoading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? "Saving..." : (editingItemId ? "Update Food Item" : "Add Food Item")}
              </button>
              {editingItemId && (
                <button
                  onClick={resetForm}
                  className="w-full mt-3 py-3 rounded-xl border border-gray-300 text-gray-600 font-semibold hover:bg-gray-100 transition-all duration-300"
                  type="button"
                >
                  Cancel Edit
                </button>
              )}
            </div>
          </form>

          <div className="mt-12">
            <div className="flex flex-wrap gap-4 justify-between items-center mb-6">
              <h3 className="text-2xl font-bold text-gray-700">All Food Items</h3>
              <div className="flex flex-wrap gap-4">
                <input
                  type="text"
                  placeholder="Search by name..."
                  value={filters.search}
                  onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                  className="p-2 border border-gray-300 rounded-lg"
                />
                <select value={filters.category} onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))} className="p-2 border border-gray-300 rounded-lg">
                  <option value="all">All Categories</option>
                  {categories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
                </select>
                <select value={filters.availability} onChange={(e) => setFilters(prev => ({ ...prev, availability: e.target.value }))} className="p-2 border border-gray-300 rounded-lg">
                  <option value="all">All Statuses</option>
                  <option value="available">Available</option>
                  <option value="unavailable">Unavailable</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredFoodItems.map((item) => (
                <motion.div
                  key={item.id}
                  className="bg-gray-50 rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 flex flex-col"
                  whileHover={{ y: -5 }}
                >
                  <div className="relative">
                    <img
                      src={item.images?.[0] ? getImageUrl(item.images[0].image_url) : 'https://placehold.co/400x300/e2e8f0/a0aec0?text=No+Image'}
                      alt={item.name}
                      className="h-48 w-full object-cover rounded-t-2xl"
                    />
                    <span className={`absolute top-2 right-2 px-3 py-1 text-xs font-semibold text-white rounded-full ${item.available ? "bg-green-500" : "bg-red-500"}`}>
                      {item.available ? "Available" : "Unavailable"}
                    </span>
                  </div>
                  <div className="p-5 flex flex-col flex-grow">
                    <div className="flex justify-between items-start">
                      <h4 className="font-bold text-lg text-gray-800">{item.name}</h4>
                      <p className="text-indigo-600 font-bold text-xl">₹{item.price}</p>
                    </div>
                    <p className="text-sm text-gray-500 mb-2">{categories.find(c => c.id === item.category_id)?.name || 'Uncategorized'}</p>
                    <p className="text-sm text-gray-600 flex-grow">{item.description}</p>
                    <div className="mt-auto pt-4 border-t border-gray-200 flex flex-col gap-2">
                      <div className="flex justify-between gap-2">
                        <button onClick={() => handleEdit(item)} className="w-1/2 bg-blue-100 text-blue-700 text-sm font-semibold py-2 rounded-lg hover:bg-blue-200 transition">Edit</button>
                        <button onClick={() => handleDelete(item.id)} className="w-1/2 bg-red-100 text-red-700 text-sm font-semibold py-2 rounded-lg hover:bg-red-200 transition">Delete</button>
                      </div>
                      <button onClick={() => toggleAvailability(item)} className="w-full bg-yellow-100 text-yellow-800 text-sm font-semibold py-2 rounded-lg hover:bg-yellow-200 transition">Toggle Status</button>
                    </div>
                  </div>
                </motion.div>
              ))}
              {filteredFoodItems.length === 0 && (
                <p className="text-center text-gray-500 mt-4 col-span-full">No food items match the current filters.</p>
              )}
            </div>
          </div>
        </div>

        {/* ====================================================== */}
        {/* Food Category Management Section */}
        {/* ====================================================== */}
        <div className="bg-white p-8 rounded-2xl shadow-lg">
          <h2 className="text-2xl font-bold mb-6 text-gray-800">🏷️ Food Category Management</h2>
          <form
            onSubmit={handleCategorySubmit}
            className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center"
          >
            <div className="md:col-span-2">
              <h3 className="text-xl font-semibold mb-4 text-gray-700">
                {editCategoryId ? "Edit Food Category" : "Add New Food Category"}
              </h3>
              <input
                type="text"
                placeholder="Category Name"
                value={categoryName}
                onChange={(e) => setCategoryName(e.target.value)}
                className="w-full border border-gray-300 rounded-xl px-4 py-3 mb-4 focus:ring-2 focus:ring-indigo-500 transition duration-200"
                required
              />
              <label className="block text-gray-700 font-medium mb-2">Category Image</label>
              <input
                type="file"
                accept="image/*"
                onChange={handleCategoryImageChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
              />
              <button
                type="submit"
                className={`w-full text-white font-bold py-3 mt-8 rounded-xl shadow-lg transition duration-300 ${isLoading ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'}`}
                disabled={isLoading}
              >
                {isLoading ? "Saving..." : (editCategoryId ? "Update Category" : "Add Category")}
              </button>
              {editCategoryId && (
                <button
                  onClick={() => { setEditCategoryId(null); setCategoryName(""); setCategoryImageFile(null); setCategoryPreviewUrl(null); }}
                  className="w-full mt-3 py-3 rounded-xl border border-gray-300 text-gray-600 font-semibold hover:bg-gray-100 transition-all duration-300"
                  type="button"
                >
                  Cancel Edit
                </button>
              )}
            </div>

            <div className="flex justify-center items-center w-full md:w-48 h-48 bg-gray-100 rounded-2xl shadow-inner overflow-hidden">
              {categoryPreviewUrl ? (
                <img src={categoryPreviewUrl} alt="Preview" className="w-full h-full object-cover" />
              ) : (
                <p className="text-gray-500 text-center px-2 text-sm">No image selected</p>
              )}
            </div>
          </form>

          <div className="mt-12">
            <h3 className="text-xl font-bold mb-6 text-gray-700">All Categories</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {categories.map((cat) => (
                <motion.div
                  key={cat.id}
                  className="bg-gray-50 rounded-2xl shadow-md hover:shadow-xl transition-all duration-300 relative flex flex-col items-center group p-4"
                  whileHover={{ y: -5 }}
                >
                  <img
                    src={getImageUrl(`static/food_categories/${cat.image}`)}
                    alt={cat.name}
                    className="w-24 h-24 object-cover rounded-full mb-3 border-4 border-white shadow-lg"
                  />
                  <p className="font-semibold text-center text-gray-800">{cat.name}</p>
                  <div className="absolute top-2 right-2 flex flex-col gap-2 transition-all duration-300 opacity-0 group-hover:opacity-100">
                    <button
                      onClick={() => handleCategoryEdit(cat)}
                      className="bg-blue-600 text-white w-8 h-8 flex items-center justify-center rounded-full shadow hover:bg-blue-700"
                    >
                      <i className="fas fa-pencil-alt text-xs"></i>
                    </button>
                    <button
                      onClick={() => handleCategoryDelete(cat.id)}
                      className="bg-red-600 text-white w-8 h-8 flex items-center justify-center rounded-full shadow hover:bg-red-700"
                    >
                      <i className="fas fa-trash-alt text-xs"></i>
                    </button>
                  </div>
                </motion.div>
              ))}
              {categories.length === 0 && (
                <p className="text-center text-gray-500 mt-4 col-span-full">No categories found.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default FoodManagement;