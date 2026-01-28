import 'package:flutter/material.dart';
import 'package:orchid_employee/data/models/food_management_model.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:dio/dio.dart';

class FoodManagementProvider with ChangeNotifier {
  final ApiService _apiService;

  List<FoodCategory> _categories = [];
  List<FoodItem> _items = [];
  bool _isLoading = false;
  String? _error;

  FoodManagementProvider(this._apiService);

  List<FoodCategory> get categories => _categories;
  List<FoodItem> get items => _items;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> fetchAllManagementData({bool force = false}) async {
    if (!force && _categories.isNotEmpty && _items.isNotEmpty) return;
    if (_isLoading) return;
    _isLoading = true;
    _error = null;
    
    try {
      final results = await Future.wait([
        _apiService.getFoodCategories(),
        _apiService.getFoodItems(),
      ]);

      if (results[0].statusCode == 200) {
        final data = results[0].data;
        print("Categories API Data: $data (Type: ${data.runtimeType})");
        List<dynamic> list = [];
        if (data is List) {
          list = data;
        } else if (data is Map) {
          list = data['data'] ?? data['categories'] ?? [];
        }
        _categories = list.map((json) => FoodCategory.fromJson(json)).toList();
      }

      if (results[1].statusCode == 200) {
        final data = results[1].data;
        print("Items API Data: $data (Type: ${data.runtimeType})");
        List<dynamic> list = [];
        if (data is List) {
          list = data;
        } else if (data is Map) {
          list = data['data'] ?? data['items'] ?? data['food_items'] ?? [];
        }
        _items = list.map((json) => FoodItem.fromJson(json)).toList();
      }
    } catch (e, stack) {
      _error = e.toString();
      print("Error fetching management data: $e");
      print(stack);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchCategories() async {
    if (_isLoading) return;
    _isLoading = true;
    _error = null;

    try {
      final response = await _apiService.getFoodCategories();
      if (response.statusCode == 200) {
        final data = response.data;
        List<dynamic> list = [];
        if (data is List) {
          list = data;
        } else if (data is Map) {
          list = data['data'] ?? data['categories'] ?? [];
        }
        _categories = list.map((json) => FoodCategory.fromJson(json)).toList();
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> fetchItems() async {
    if (_isLoading) return;
    _isLoading = true;
    _error = null;

    try {
      final response = await _apiService.getFoodItems();
      if (response.statusCode == 200) {
        final data = response.data;
        List<dynamic> list = [];
        if (data is List) {
          list = data;
        } else if (data is Map) {
          list = data['data'] ?? data['items'] ?? data['food_items'] ?? [];
        }
        _items = list.map((json) => FoodItem.fromJson(json)).toList();
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> toggleAvailability(int itemId, bool currentStatus) async {
    try {
      final response = await _apiService.updateFoodItem(itemId, {
        'available': !currentStatus,
      });
      if (response.statusCode == 200) {
        final index = _items.indexWhere((item) => item.id == itemId);
        if (index != -1) {
          final updatedItem = FoodItem(
            id: _items[index].id,
            name: _items[index].name,
            description: _items[index].description,
            price: _items[index].price,
            roomServicePrice: _items[index].roomServicePrice,
            categoryId: _items[index].categoryId,
            available: !currentStatus,
            alwaysAvailable: _items[index].alwaysAvailable,
            images: _items[index].images,
          );
          _items[index] = updatedItem;
          notifyListeners();
        }
        return true;
      }
    } catch (e) {
      print("Error toggling availability: $e");
    }
    return false;
  }

  Future<bool> addCategory(String name, {MultipartFile? image}) async {
    try {
      final formData = FormData.fromMap({
        'name': name,
        if (image != null) 'image': image,
      });
      final response = await _apiService.createFoodCategory(formData);
      if (response.statusCode == 200 || response.statusCode == 201) {
        await fetchCategories();
        return true;
      }
    } catch (e) {
      print("Error adding category: $e");
    }
    return false;
  }

  Future<bool> updateCategory(int id, String name, {MultipartFile? image}) async {
    try {
      final formData = FormData.fromMap({
        'name': name,
        if (image != null) 'image': image,
      });
      final response = await _apiService.updateFoodCategory(id, formData);
      if (response.statusCode == 200) {
        await fetchCategories();
        return true;
      }
    } catch (e) {
      print("Error updating category: $e");
    }
    return false;
  }

  Future<bool> addItem(Map<String, dynamic> data, {List<MultipartFile>? images}) async {
    try {
      final formData = FormData.fromMap(data);
      if (images != null) {
        for (var file in images) {
          formData.files.add(MapEntry('images', file));
        }
      }
      final response = await _apiService.createFoodItem(formData);
      if (response.statusCode == 200 || response.statusCode == 201) {
        await fetchItems();
        return true;
      }
    } catch (e) {
      print("Error adding item: $e");
    }
    return false;
  }

  Future<bool> updateItem(int id, Map<String, dynamic> data) async {
    try {
      final response = await _apiService.updateFoodItem(id, data);
      if (response.statusCode == 200) {
        await fetchItems();
        return true;
      }
    } catch (e) {
      print("Error updating item: $e");
    }
    return false;
  }

  Future<bool> deleteItem(int itemId) async {
    try {
      final response = await _apiService.deleteFoodItem(itemId);
      if (response.statusCode == 200) {
        _items.removeWhere((item) => item.id == itemId);
        notifyListeners();
        return true;
      }
    } catch (e) {
      print("Error deleting item: $e");
    }
    return false;
  }

  Future<bool> deleteCategory(int categoryId) async {
    try {
      final response = await _apiService.deleteFoodCategory(categoryId);
      if (response.statusCode == 200) {
        _categories.removeWhere((cat) => cat.id == categoryId);
        notifyListeners();
        return true;
      }
    } catch (e) {
      print("Error deleting category: $e");
    }
    return false;
  }
}
