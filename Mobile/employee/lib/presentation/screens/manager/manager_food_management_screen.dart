import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/food_management_provider.dart';
import 'package:orchid_employee/data/models/food_management_model.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';

class ManagerFoodManagementScreen extends StatefulWidget {
  const ManagerFoodManagementScreen({super.key});

  @override
  State<ManagerFoodManagementScreen> createState() => _ManagerFoodManagementScreenState();
}

class _ManagerFoodManagementScreenState extends State<ManagerFoodManagementScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FoodManagementProvider>().fetchCategories();
      context.read<FoodManagementProvider>().fetchItems();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Food Management"),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: "Items"),
            Tab(text: "Categories"),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              context.read<FoodManagementProvider>().fetchCategories();
              context.read<FoodManagementProvider>().fetchItems();
            },
          ),
        ],
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildItemsList(),
          _buildCategoriesList(),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          if (_tabController.index == 0) {
            _showItemForm();
          } else {
            _showCategoryForm();
          }
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showCategoryForm({FoodCategory? category}) {
    final bool isEditing = category != null;
    final nameController = TextEditingController(text: category?.name ?? "");
    
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 16, right: 16, top: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(isEditing ? "Edit Category" : "Add Category", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextField(controller: nameController, decoration: const InputDecoration(labelText: "Category Name", border: OutlineInputBorder())),
            const SizedBox(height: 16),
            const Text("Image upload currently only supported via web dashboard.", style: TextStyle(fontSize: 12, color: Colors.grey)),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  // Future: API call to save
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Save coming soon.")));
                  Navigator.pop(ctx);
                },
                child: const Text("Save"),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  void _showItemForm({FoodItem? item}) {
    // Similar form for items
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Detailed item form coming soon.")));
  }

  Widget _buildItemsList() {
    return Consumer<FoodManagementProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading && provider.items.isEmpty) {
          return const ListSkeleton();
        }
        if (provider.items.isEmpty) {
          return const Center(child: Text("No food items found"));
        }

        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: provider.items.length,
          itemBuilder: (context, index) {
            final item = provider.items[index];
            return _buildFoodItemCard(item);
          },
        );
      },
    );
  }

  Widget _buildFoodItemCard(FoodItem item) {
    final String? firstImageUrl = item.images.isNotEmpty ? item.images[0].imageUrl : null;
    final String fullImageUrl = firstImageUrl != null
        ? '${ApiConstants.imageBaseUrl}/${firstImageUrl.startsWith('/') ? firstImageUrl.substring(1) : firstImageUrl}'
        : '';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: firstImageUrl != null
                  ? Image.network(
                      fullImageUrl,
                      width: 60,
                      height: 60,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) =>
                          Container(width: 60, height: 60, color: Colors.grey[200], child: const Icon(Icons.fastfood)),
                    )
                  : Container(width: 60, height: 60, color: Colors.grey[200], child: const Icon(Icons.fastfood)),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                  Text("Dine-in: ₹${item.price.toStringAsFixed(0)}", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                  Text("Room Svc: ₹${item.roomServicePrice.toStringAsFixed(0)}", style: TextStyle(color: Colors.grey[600], fontSize: 13)),
                ],
              ),
            ),
            Switch(
              value: item.available,
              onChanged: (val) {
                context.read<FoodManagementProvider>().toggleAvailability(item.id, item.available);
              },
              activeColor: Colors.green,
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline, color: Colors.red),
              onPressed: () => _confirmDeleteDiscovery(item.id, true),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoriesList() {
    return Consumer<FoodManagementProvider>(
      builder: (context, provider, _) {
        if (provider.isLoading && provider.categories.isEmpty) {
          return const ListSkeleton();
        }
        if (provider.categories.isEmpty) {
          return const Center(child: Text("No categories found"));
        }

        return GridView.builder(
          padding: const EdgeInsets.all(16),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.3,
          ),
          itemCount: provider.categories.length,
          itemBuilder: (context, index) {
            final cat = provider.categories[index];
            return _buildCategoryCard(cat);
          },
        );
      },
    );
  }

  Widget _buildCategoryCard(FoodCategory cat) {
    final String fullImageUrl = cat.image != null
        ? '${ApiConstants.imageBaseUrl}/uploads/food_categories/${cat.image}'
        : '';

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey[200]!),
      ),
      child: Stack(
        children: [
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const SizedBox(height: 8),
              if (cat.image != null)
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(8),
                    child: Image.network(
                      fullImageUrl,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) => const Icon(Icons.category, size: 40),
                    ),
                  ),
                )
              else
                const Icon(Icons.category, size: 40, color: Colors.grey),
              const SizedBox(height: 8),
              Text(cat.name, style: const TextStyle(fontWeight: FontWeight.bold), textAlign: TextAlign.center),
              const SizedBox(height: 8),
            ],
          ),
          Positioned(
            top: 0,
            right: 0,
            child: IconButton(
              icon: const Icon(Icons.cancel, color: Colors.red, size: 20),
              onPressed: () => _confirmDeleteDiscovery(cat.id, false),
            ),
          ),
        ],
      ),
    );
  }

  void _confirmDeleteDiscovery(int id, bool isItem) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text("Delete ${isItem ? 'Item' : 'Category'}?"),
        content: const Text("This action cannot be undone."),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              bool success;
              if (isItem) {
                success = await context.read<FoodManagementProvider>().deleteItem(id);
              } else {
                success = await context.read<FoodManagementProvider>().deleteCategory(id);
              }
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(success ? "Deleted successfully" : "Failed to delete")),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red, foregroundColor: Colors.white),
            child: const Text("Delete"),
          ),
        ],
      ),
    );
  }
}
