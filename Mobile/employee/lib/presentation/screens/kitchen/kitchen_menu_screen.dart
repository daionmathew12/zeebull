import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:orchid_employee/presentation/providers/kitchen_provider.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';

class KitchenMenuScreen extends StatefulWidget {
  const KitchenMenuScreen({super.key});

  @override
  State<KitchenMenuScreen> createState() => _KitchenMenuScreenState();
}

class _KitchenMenuScreenState extends State<KitchenMenuScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<KitchenProvider>().fetchFoodItems();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        title: const Text("Kitchen Menu"),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: Consumer<KitchenProvider>(
        builder: (context, kitchen, child) {
          if (kitchen.isLoading && kitchen.foodItems.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          final totalItems = kitchen.foodItems.length;
          final availableItems = kitchen.foodItems.where((i) {
            final dynamic raw = i['available'];
            return raw == true || raw == 'true' || raw == 1 || raw == '1';
          }).length;
          final categories = kitchen.foodItems.map((i) => i['category_name']).toSet().length;

          return Column(
            children: [
              _buildKpiSection(totalItems, availableItems, categories),
              Expanded(
                child: kitchen.foodItems.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.restaurant_menu, size: 64, color: Colors.grey.shade300),
                            const SizedBox(height: 16),
                            const Text("No menu items found", style: TextStyle(color: Colors.grey)),
                          ],
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: () => kitchen.fetchFoodItems(),
                        child: ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: kitchen.foodItems.length,
                          itemBuilder: (context, index) {
                            final item = kitchen.foodItems[index];
                            return _buildMenuItemCard(item);
                          },
                        ),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildKpiSection(int total, int available, int catCount) {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: Row(
        children: [
          _buildKpiCard("Total Items", total.toString(), Colors.blue),
          const SizedBox(width: 8),
          _buildKpiCard("Available", available.toString(), Colors.green),
          const SizedBox(width: 8),
          _buildKpiCard("Categories", catCount.toString(), Colors.purple),
        ],
      ),
    );
  }

  Widget _buildKpiCard(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.05),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.1)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 2),
            Text(label, style: TextStyle(fontSize: 10, color: color.withOpacity(0.6), fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItemCard(dynamic item) {
    final dynamic availRaw = item['available'];
    final bool available = availRaw == true || availRaw == 'true' || availRaw == 1 || availRaw == '1';
    
    // images is a List of Maps with 'image_url'
    String? imageUrl;
    if (item['images'] != null && (item['images'] as List).isNotEmpty) {
      final firstImage = item['images'][0];
      if (firstImage is Map) {
        imageUrl = firstImage['image_url'];
      } else {
        imageUrl = firstImage.toString();
      }
    }

    // category is a Map with 'name'
    final String categoryName = item['category_name'] ?? 
                               (item['category'] is Map ? item['category']['name'] : "General");

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: Colors.grey.shade100,
                borderRadius: BorderRadius.circular(12),
                image: imageUrl != null && imageUrl.isNotEmpty
                    ? DecorationImage(
                        image: NetworkImage("${ApiConstants.imageBaseUrl}$imageUrl"),
                        fit: BoxFit.cover,
                      )
                    : null,
              ),
              child: (imageUrl == null || imageUrl.isEmpty) ? Icon(Icons.fastfood, color: Colors.grey.shade400) : null,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(item['name'] ?? "Unknown", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text(
                        "₹${item['price']}",
                        style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.blue, fontSize: 16),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    categoryName,
                    style: TextStyle(color: Colors.grey.shade500, fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    item['description'] ?? "",
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: (available ? Colors.green : Colors.red).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      available ? "AVAILABLE" : "OUT OF STOCK",
                      style: TextStyle(
                        color: available ? Colors.green : Colors.red,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
