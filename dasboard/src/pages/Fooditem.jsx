import React, { useEffect, useState } from "react";
import DashboardLayout from "../layout/DashboardLayout";
import API from "../services/api";
import { normalizeQuantity } from "../utils/quantityValidation";
import { ChefHat, Plus, X, ChevronDown, ChevronUp, Clock, IndianRupee } from "lucide-react";

import { toast } from "react-hot-toast";
import imageCompression from 'browser-image-compression';

import { motion } from "framer-motion";
import { getImageUrl } from "../utils/imageUtils";

const bgColors = [
  "bg-red-50",
  "bg-green-50",
  "bg-yellow-50",
  "bg-blue-100",
  "bg-purple-50",
  "bg-pink-50",
  "bg-orange-50",
];

const FoodItems = () => {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [images, setImages] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);
  const [foodItems, setFoodItems] = useState([]);
  const [editingItemId, setEditingItemId] = useState(null);
  const [available, setAvailable] = useState(true);
  const [alwaysAvailable, setAlwaysAvailable] = useState(false);
  const [availableFromTime, setAvailableFromTime] = useState("");
  const [availableToTime, setAvailableToTime] = useState("");
  const [timeWisePrices, setTimeWisePrices] = useState([]);
  const [isCompressing, setIsCompressing] = useState(false);

  // Recipe/Ingredients state
  const [showIngredients, setShowIngredients] = useState(false);
  const [recipeName, setRecipeName] = useState("");
  const [recipeDescription, setRecipeDescription] = useState("");
  const [servings, setServings] = useState(1);
  const [prepTime, setPrepTime] = useState("");
  const [cookTime, setCookTime] = useState("");
  const [ingredients, setIngredients] = useState([]);
  const [inventoryItems, setInventoryItems] = useState([]);

  const token = localStorage.getItem("token");

  useEffect(() => {
    fetchCategories();
    fetchFoodItems();
    fetchInventoryItems();
  }, []);

  useEffect(() => {
    if (name && !recipeName && !editingItemId) {
      setRecipeName(name);
    }
  }, [name]);

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
      const res = await API.get("/food-items/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setFoodItems(res.data);
    } catch (err) {
      console.error("Failed to fetch items", err);
    }
  };

  const fetchInventoryItems = async () => {
    try {
      const res = await API.get("/inventory/items?limit=1000");
      setInventoryItems(res.data || []);
    } catch (err) {
      console.error("Failed to fetch inventory items", err);
      setInventoryItems([]);
    }
  };

  const handleImageChange = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setIsCompressing(true);
    const toastId = toast.loading("Compressing images...");

    try {
      const compressedFiles = await Promise.all(
        files.map(async (file) => {
          if (!file.type.startsWith('image/')) return file;
          const options = { maxSizeMB: 15, maxWidthOrHeight: 1920, useWebWorker: true };
          try {
            return await imageCompression(file, options);
          } catch (error) {
            console.error("Compression failed for", file.name, error);
            return file;
          }
        })
      );

      setImages((prevImages) => [...prevImages, ...compressedFiles]);
      const newPreviews = compressedFiles.map((file) => URL.createObjectURL(file));
      setImagePreviews((prev) => [...prev, ...newPreviews]);
      toast.success("Images ready!", { id: toastId });
    } catch (err) {
      console.error(err);
      toast.error("Error processing images", { id: toastId });
    } finally {
      setIsCompressing(false);
      e.target.value = '';
    }
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
    setAlwaysAvailable(item.always_available === true);
    setAvailableFromTime(item.available_from_time || "");
    setAvailableToTime(item.available_to_time || "");
    
    let twp = item.time_wise_prices || [];
    if (typeof twp === 'string') {
      try { twp = JSON.parse(twp); } catch (e) { twp = []; }
    }
    setTimeWisePrices(twp);

    setImagePreviews(item.images?.map((img) => getImageUrl(img.image_url)) || []);
    setImages([]);
    setShowIngredients(false);
    setRecipeName("");
    setRecipeDescription("");
    setServings(1);
    setPrepTime("");
    setCookTime("");
    setIngredients([]);
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
    setAlwaysAvailable(false);
    setAvailableFromTime("");
    setAvailableToTime("");
    setTimeWisePrices([]);
    setShowIngredients(false);
    setRecipeName("");
    setRecipeDescription("");
    setServings(1);
    setPrepTime("");
    setCookTime("");
    setIngredients([]);
  };

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

  const handleAddIngredient = () => {
    setIngredients([...ingredients, { inventory_item_id: "", quantity: "", unit: "pcs", notes: "" }]);
  };

  const handleIngredientChange = (index, field, value) => {
    const updated = [...ingredients];
    if (field === "quantity") {
      const currentUnit = updated[index].unit;
      updated[index][field] = normalizeQuantity(value, currentUnit);
    } else {
      updated[index][field] = value;
    }
    if (field === "inventory_item_id" && value) {
      const invItem = inventoryItems.find(item => item.id === parseInt(value));
      if (invItem && invItem.unit) {
        updated[index].unit = invItem.unit;
      }
    }
    setIngredients(updated);
  };

  const handleRemoveIngredient = (index) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("name", name);
    formData.append("description", description);
    formData.append("price", price);
    formData.append("category_id", selectedCategory);
    formData.append("available", available);
    formData.append("always_available", alwaysAvailable);
    if (!alwaysAvailable) {
        if (availableFromTime) formData.append("available_from_time", availableFromTime);
        if (availableToTime) formData.append("available_to_time", availableToTime);
    }
    formData.append("time_wise_prices", JSON.stringify(timeWisePrices));
    images.forEach((img) => formData.append("images", img));

    try {
      let foodItemId;
      if (editingItemId) {
        await API.put(`/food-items/${editingItemId}/`, formData, {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
        });
        foodItemId = editingItemId;
      } else {
        const response = await API.post("/food-items/", formData, {
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
        });
        foodItemId = response.data.id;
      }

      if (showIngredients && ingredients.length > 0 && foodItemId) {
        try {
          const recipeData = {
            food_item_id: foodItemId,
            name: recipeName || name,
            description: recipeDescription || description,
            servings: parseInt(servings) || 1,
            prep_time_minutes: prepTime ? parseInt(prepTime) : null,
            cook_time_minutes: cookTime ? parseInt(cookTime) : null,
            ingredients: ingredients
              .filter(ing => ing.inventory_item_id && ing.quantity)
              .map(ing => ({
                inventory_item_id: parseInt(ing.inventory_item_id),
                quantity: parseFloat(ing.quantity),
                unit: ing.unit || "pcs",
                notes: ing.notes || ""
              }))
          };
          if (recipeData.ingredients.length > 0) {
            await API.post("/recipes", recipeData);
          }
        } catch (recipeErr) {
          console.error("Failed to create recipe:", recipeErr);
          toast.error("Food item saved, but recipe failed.");
        }
      }

      toast.success("Food item saved successfully!");
      fetchFoodItems();
      resetForm();
    } catch (err) {
      console.error("Failed to save food item", err);
      toast.error("Failed to save food item.");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this item?")) return;
    try {
      await API.delete(`/food-items/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      fetchFoodItems();
      toast.success("Item deleted");
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  const toggleAvailability = async (item) => {
    try {
      await API.patch(
        `/food-items/${item.id}/toggle-availability?available=${!item.available}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchFoodItems();
    } catch (err) {
      console.error("Failed to toggle availability", err);
    }
  };

  return (
    <DashboardLayout>
      <div className="p-6 flex flex-col items-center gap-8">
        <form
          onSubmit={handleSubmit}
          className="bg-white shadow-xl rounded-3xl p-8 flex flex-col items-center gap-8 w-full max-w-4xl"
        >
          <div className="w-full">
            <h2 className="text-2xl font-black mb-6 text-slate-800 text-center md:text-left flex items-center gap-3">
              <div className="w-2 h-8 bg-indigo-600 rounded-full"></div>
              {editingItemId ? "Edit Food Item" : "Create New Food Item"}
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div className="space-y-4">
                    <input
                      type="text"
                      placeholder="Item Name"
                      className="w-full border-2 border-slate-100 rounded-2xl px-5 py-4 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all font-bold placeholder:text-slate-400"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                    <textarea
                      placeholder="Describe what makes this item special..."
                      className="w-full border-2 border-slate-100 rounded-3xl px-5 py-4 focus:ring-2 focus:ring-indigo-500 transition-all font-medium min-h-[120px] resize-none"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      required
                    />
                </div>
                <div className="space-y-4">
                    <div className="relative">
                        <IndianRupee size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input
                          type="number"
                          placeholder="Base Price"
                          className="w-full border-2 border-slate-100 rounded-2xl pl-12 pr-5 py-4 focus:ring-2 focus:ring-indigo-500 font-black text-slate-800"
                          value={price}
                          onChange={(e) => setPrice(e.target.value)}
                          required
                        />
                    </div>
                    <select
                      className="w-full border-2 border-slate-100 rounded-2xl px-5 py-4 focus:ring-2 focus:ring-indigo-500 font-bold text-slate-700 bg-white"
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      required
                    >
                      <option value="">Choose Category</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                      ))}
                    </select>

                    <div className="bg-slate-50 p-4 rounded-3xl space-y-3">
                        <div className="flex items-center justify-between">
                            <label className="flex items-center gap-3 cursor-pointer group">
                              <input
                                type="checkbox"
                                className="w-6 h-6 rounded-lg text-indigo-600 focus:ring-indigo-500 border-slate-300"
                                checked={available}
                                onChange={() => setAvailable(!available)}
                              />
                              <span className="font-bold text-slate-700 group-hover:text-indigo-600 transition-colors">Active for Ordering</span>
                            </label>
                            <label className="flex items-center gap-3 cursor-pointer group">
                              <input
                                type="checkbox"
                                className="w-6 h-6 rounded-lg text-amber-500 focus:ring-amber-500 border-slate-300"
                                checked={alwaysAvailable}
                                onChange={() => setAlwaysAvailable(!alwaysAvailable)}
                              />
                              <span className="font-bold text-slate-700 group-hover:text-amber-600 transition-colors">Available 24/7</span>
                            </label>
                        </div>
                        
                        {!alwaysAvailable && (
                            <div className="grid grid-cols-2 gap-3 animate-in fade-in slide-in-from-top-2">
                                <div>
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1 mb-1 block">From</label>
                                    <input type="time" className="w-full border-none bg-white rounded-xl px-3 py-2 text-sm font-bold shadow-sm" value={availableFromTime} onChange={(e) => setAvailableFromTime(e.target.value)} />
                                </div>
                                <div>
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1 mb-1 block">To</label>
                                    <input type="time" className="w-full border-none bg-white rounded-xl px-3 py-2 text-sm font-bold shadow-sm" value={availableToTime} onChange={(e) => setAvailableToTime(e.target.value)} />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Time-wise Pricing */}
            <div className="mb-6 bg-indigo-50/50 p-6 rounded-3xl border border-indigo-100">
                <div className="flex justify-between items-center mb-4">
                  <h4 className="font-black text-indigo-900 flex items-center gap-2">
                    <Clock size={18} />
                    Time-based Pricing
                  </h4>
                  <button type="button" onClick={handleAddTimeWisePrice} className="bg-indigo-600 text-white p-2 rounded-xl hover:bg-indigo-700 transition-all shadow-md">
                    <Plus size={18} />
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {timeWisePrices.map((tp, idx) => (
                    <div key={idx} className="bg-white p-3 rounded-2xl flex items-end gap-2 shadow-sm border border-indigo-50 relative group">
                        <button type="button" onClick={() => handleRemoveTimeWisePrice(idx)} className="absolute -top-2 -right-2 bg-red-100 text-red-600 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-all">
                            <X size={12} />
                        </button>
                        <div className="flex-1">
                            <label className="text-[9px] font-black text-slate-400 uppercase tracking-tighter block mb-0.5">Time Range</label>
                            <div className="flex items-center gap-1">
                                <input type="time" className="w-full border-none bg-slate-50 rounded-lg p-1 text-[11px]" value={tp.from_time} onChange={(e) => handleUpdateTimeWisePrice(idx, "from_time", e.target.value)} />
                                <span className="text-slate-400">-</span>
                                <input type="time" className="w-full border-none bg-slate-50 rounded-lg p-1 text-[11px]" value={tp.to_time} onChange={(e) => handleUpdateTimeWisePrice(idx, "to_time", e.target.value)} />
                            </div>
                        </div>
                        <div className="w-20">
                            <label className="text-[9px] font-black text-slate-400 uppercase tracking-tighter block mb-0.5">Price (₹)</label>
                            <input type="number" className="w-full border-none bg-indigo-50/50 rounded-lg p-1 text-[11px] font-black" value={tp.price} onChange={(e) => handleUpdateTimeWisePrice(idx, "price", e.target.value)} />
                        </div>
                    </div>
                  ))}
                  {timeWisePrices.length === 0 && <p className="col-span-2 text-center text-indigo-300 text-xs italic py-4">No variable pricing set</p>}
                </div>
            </div>

            <div className="mb-6">
                <label className="block text-sm font-black text-slate-700 mb-3">Item Photos</label>
                <div className="flex flex-wrap gap-4">
                    <label className="w-24 h-24 border-2 border-dashed border-slate-200 rounded-3xl flex flex-col items-center justify-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all group">
                        <Plus className="text-slate-300 group-hover:text-indigo-400" />
                        <span className="text-[10px] font-black text-slate-300 group-hover:text-indigo-400 uppercase tracking-widest mt-1">Add</span>
                        <input type="file" accept="image/*" multiple onChange={handleImageChange} className="hidden" />
                    </label>
                    {imagePreviews.map((src, index) => (
                      <div key={index} className="relative group w-24 h-24">
                        <img src={src} alt="Preview" className="w-full h-full object-cover rounded-3xl shadow-md" />
                        <button type="button" onClick={() => handleRemoveImage(index)} className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full p-1 shadow-lg transform scale-0 group-hover:scale-100 transition-all">
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                </div>
            </div>

            <div className="border-t border-slate-100 pt-6 mt-6">
              <button
                type="button"
                onClick={() => setShowIngredients(!showIngredients)}
                className={`w-full flex items-center justify-between p-5 rounded-3xl transition-all ${showIngredients ? 'bg-slate-800 text-white' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'}`}
              >
                <span className="flex items-center gap-3 font-black uppercase tracking-widest text-xs">
                  <ChefHat size={18} />
                  Kitchen Recipe & Ingredients
                </span>
                {showIngredients ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </button>

              {showIngredients && (
                <div className="mt-4 space-y-6 p-6 bg-slate-50 rounded-3xl border border-slate-100 animate-in zoom-in-95">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 block pl-1">Servings</label>
                      <input type="number" min="1" className="w-full border-none rounded-2xl px-4 py-3 font-bold" value={servings} onChange={(e) => setServings(e.target.value)} />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 block pl-1">Prep (Mins)</label>
                            <input type="number" min="0" className="w-full border-none rounded-2xl px-4 py-3 font-bold" value={prepTime} onChange={(e) => setPrepTime(e.target.value)} />
                        </div>
                        <div>
                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1 block pl-1">Cook (Mins)</label>
                            <input type="number" min="0" className="w-full border-none rounded-2xl px-4 py-3 font-bold" value={cookTime} onChange={(e) => setCookTime(e.target.value)} />
                        </div>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-xs font-black text-slate-700 uppercase tracking-widest">Ingredients List</h5>
                      <button type="button" onClick={handleAddIngredient} className="text-xs font-black bg-indigo-600 text-white px-4 py-2 rounded-xl hover:bg-indigo-700 transition-all flex items-center gap-2">
                        <Plus size={14} /> Add
                      </button>
                    </div>

                    <div className="space-y-3">
                      {ingredients.map((ingredient, index) => (
                        <div key={index} className="grid grid-cols-12 gap-2 items-end p-4 bg-white rounded-2xl border border-slate-100 relative group animate-in slide-in-from-right-4">
                           <button type="button" onClick={() => handleRemoveIngredient(index)} className="absolute -top-2 -right-2 bg-red-100 text-red-600 rounded-full p-1 opacity-0 group-hover:opacity-100 transition-all">
                            <X size={12} />
                          </button>
                          <div className="col-span-6">
                            <select className="w-full border-none bg-slate-50 rounded-xl px-3 py-2 text-xs font-bold" value={ingredient.inventory_item_id} onChange={(e) => handleIngredientChange(index, "inventory_item_id", e.target.value)} required>
                              <option value="">Select Item</option>
                              {inventoryItems.map((item) => (
                                <option key={item.id} value={item.id}>{item.name}</option>
                              ))}
                            </select>
                          </div>
                          <div className="col-span-3">
                            <input type="number" placeholder="Qty" className="w-full border-none bg-slate-50 rounded-xl px-3 py-2 text-xs font-bold text-center" value={ingredient.quantity} onChange={(e) => handleIngredientChange(index, "quantity", e.target.value)} required />
                          </div>
                          <div className="col-span-3">
                            <input type="text" placeholder="Unit" className="w-full border-none bg-slate-50 rounded-xl px-3 py-2 text-xs font-bold text-center" value={ingredient.unit} onChange={(e) => handleIngredientChange(index, "unit", e.target.value)} required />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button className="w-full bg-slate-800 text-white font-black py-5 rounded-3xl shadow-xl hover:bg-indigo-600 hover:-translate-y-1 transform transition-all uppercase tracking-widest mt-4">
              {editingItemId ? "Update Food Entry" : "Launch New Food Item"}
            </button>
          </div>
        </form>

        <div className="w-full max-w-6xl">
            <div className="flex flex-col items-center mb-10">
                <h3 className="text-3xl font-black text-slate-800 tracking-tight">Cuisine Catalog</h3>
                <div className="w-12 h-1.5 bg-indigo-600 rounded-full mt-2"></div>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
                {foodItems.map((item, index) => (
                  <div key={item.id} className="group bg-white rounded-[40px] p-6 border-2 border-slate-50 hover:border-indigo-100 shadow-sm hover:shadow-2xl transition-all duration-500 overflow-hidden relative">
                    <div className="flex justify-between items-start mb-4">
                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${bgColors[index % bgColors.length]}`}>
                            <ChefHat className="text-slate-700" size={24} />
                        </div>
                        <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-50 rounded-full border border-slate-100">
                             <div className={`w-2 h-2 rounded-full ${item.available ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-400'}`}></div>
                             <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">{item.available ? 'Active' : 'Inactive'}</span>
                        </div>
                    </div>

                    <h4 className="font-black text-xl text-slate-800 line-clamp-1">{item.name}</h4>
                    <p className="text-slate-500 text-sm mt-2 line-clamp-2 min-h-[40px] leading-relaxed">{item.description}</p>
                    
                    <div className="flex items-end justify-between mt-6">
                        <div>
                             <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Price Point</p>
                             <div className="flex items-baseline gap-0.5">
                                <span className="text-indigo-600 font-black text-2xl">₹</span>
                                <span className="text-slate-800 font-black text-2xl">{item.price}</span>
                             </div>
                        </div>
                        <div className="flex -space-x-3">
                            {item.images?.slice(0, 3).map((img, idx) => (
                                <img key={idx} src={getImageUrl(img.image_url)} className="w-10 h-10 rounded-full border-4 border-white object-cover shadow-sm group-hover:translate-x-1 transition-transform" />
                            ))}
                            {item.images?.length > 3 && (
                                <div className="w-10 h-10 rounded-full bg-slate-100 border-4 border-white flex items-center justify-center text-[10px] font-black text-slate-500">
                                    +{item.images.length - 3}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="absolute inset-x-0 bottom-0 p-6 bg-gradient-to-t from-white via-white/95 to-transparent translate-y-full group-hover:translate-y-0 transition-transform duration-500 flex gap-2">
                         <button onClick={() => handleEdit(item)} className="flex-1 bg-slate-800 text-white rounded-2xl py-3 font-black text-xs uppercase tracking-widest hover:bg-indigo-600 transition-colors">Edit</button>
                         <button onClick={() => toggleAvailability(item)} className="px-4 bg-slate-50 text-slate-700 rounded-2xl hover:bg-indigo-50 hover:text-indigo-600 transition-all"><Clock size={16} /></button>
                         <button onClick={() => handleDelete(item.id)} className="px-4 bg-red-50 text-red-600 rounded-2xl hover:bg-red-600 hover:text-white transition-all"><X size={16} /></button>
                    </div>
                  </div>
                ))}
            </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default FoodItems;
