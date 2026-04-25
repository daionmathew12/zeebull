import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:typed_data';
import 'package:provider/provider.dart';
import 'package:flutter/foundation.dart';
import 'dart:io';
import 'package:orchid_employee/data/models/room_model.dart';
import 'package:orchid_employee/core/constants/api_constants.dart';
import 'package:orchid_employee/data/models/room_type_model.dart';
import 'package:orchid_employee/presentation/screens/manager/room_type_form_screen.dart';
import 'package:orchid_employee/presentation/providers/room_provider.dart';
import 'package:orchid_employee/data/services/api_service.dart';
import 'package:orchid_employee/presentation/widgets/skeleton_loaders.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_card.dart';
import 'package:orchid_employee/core/constants/app_colors.dart';
import 'package:orchid_employee/presentation/widgets/onyx_glass_dialog.dart';
import 'package:intl/intl.dart';
import 'dart:ui';
import 'dart:convert';
import 'package:orchid_employee/presentation/providers/package_provider.dart';
import 'package:orchid_employee/data/models/package_model.dart';

class ManagerRoomMgmtScreen extends StatefulWidget {
  final bool isClockedIn;
  
  const ManagerRoomMgmtScreen({super.key, this.isClockedIn = true});

  @override
  State<ManagerRoomMgmtScreen> createState() => _ManagerRoomMgmtScreenState();
}

class _ManagerRoomMgmtScreenState extends State<ManagerRoomMgmtScreen> {
  String _filterStatus = "all";
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = Provider.of<RoomProvider>(context, listen: false);
      provider.fetchRooms();
      provider.fetchRoomTypes();
      provider.fetchRoomStats();
      Provider.of<PackageProvider>(context, listen: false).fetchPackages();
    });
  }

  Widget _buildKpiSection(RoomProvider provider) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: Row(
        children: [
          _buildKpiCard("TOTAL", "${provider.roomStats['total'] ?? 0}", Colors.white),
          const SizedBox(width: 10),
          _buildKpiCard("OCCUPIED", "${provider.roomStats['occupied'] ?? 0}", Colors.blueAccent),
          const SizedBox(width: 10),
          _buildKpiCard("MAINT.", "${provider.roomStats['maintenance'] ?? 0}", Colors.redAccent),
        ],
      ),
    );
  }

  Widget _buildKpiCard(String label, String value, Color color) {
    return Expanded(
      child: OnyxGlassCard(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Text(label, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 9, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.w900)),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<RoomProvider>();
    final rooms = _filterStatus == "all" 
        ? provider.rooms 
        : provider.rooms.where((r) => r.status.toLowerCase() == _filterStatus).toList();

    return DefaultTabController(
      length: 4,
      child: Scaffold(
      backgroundColor: AppColors.onyx,
      body: Stack(
        children: [
          // Background Gradient
          Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: AppColors.primaryGradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
          ),

          // Ambient Glows
          Positioned(
            top: -100,
            right: -50,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.accent.withOpacity(0.1),
              ),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 100, sigmaY: 100),
                child: Container(color: Colors.transparent),
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                // Custom Header Navigation
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(
                    children: [
                      IconButton(
                        onPressed: () {
                          if (Navigator.canPop(context)) {
                            Navigator.pop(context);
                          } else {
                            Scaffold.of(context).openDrawer();
                          }
                        },
                        icon: Icon(
                          Navigator.canPop(context) ? Icons.arrow_back_ios_new : Icons.menu_rounded,
                          color: Colors.white,
                          size: Navigator.canPop(context) ? 16 : 22,
                        ),
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.white.withOpacity(0.05),
                          padding: const EdgeInsets.all(12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))
                        ),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "ROOM CONTROL",
                              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                            ),
                            Text(
                              "INVENTORY & STATUS OVERVIEW",
                              style: TextStyle(color: AppColors.accent, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 1.5),
                            ),
                          ],
                        ),
                      ),
                      PopupMenuButton<String>(
                        initialValue: _filterStatus,
                        onSelected: (value) => setState(() => _filterStatus = value),
                        color: AppColors.onyx.withOpacity(0.95),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20), side: const BorderSide(color: Colors.white10)),
                        icon: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(color: AppColors.accent.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
                          child: const Icon(Icons.tune, color: AppColors.accent, size: 20),
                        ),
                        itemBuilder: (context) => [
                          _buildFilterItem("all", "ALL DOMAINS", Icons.grid_view, Colors.white),
                          _buildFilterItem("available", "AVAILABLE", Icons.check_circle_outline, Colors.greenAccent),
                          _buildFilterItem("occupied", "OCCUPIED", Icons.person_outline, Colors.blueAccent),
                          _buildFilterItem("maintenance", "MAINTENANCE", Icons.build_outlined, Colors.redAccent),
                        ],
                      ),
                      if (widget.isClockedIn) ...[
                        const SizedBox(width: 12),
                        // Add Type Button
                        IconButton(
                          onPressed: () => _showRoomTypeDialog(),
                          icon: const Icon(Icons.category_rounded, color: Colors.blueAccent, size: 20),
                          tooltip: "ADD ROOM TYPE",
                          style: IconButton.styleFrom(
                            backgroundColor: Colors.blueAccent.withOpacity(0.1),
                            padding: const EdgeInsets.all(10),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.blueAccent.withOpacity(0.2)))
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          onPressed: () => _showRoomForm(),
                          icon: const Icon(Icons.add_rounded, color: AppColors.accent, size: 24),
                          tooltip: "ADD ROOM",
                          style: IconButton.styleFrom(
                            backgroundColor: AppColors.accent.withOpacity(0.1),
                            padding: const EdgeInsets.all(10),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: AppColors.accent.withOpacity(0.2)))
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton(
                          onPressed: () => _showPackageForm(),
                          icon: const Icon(Icons.loyalty_rounded, color: Colors.amberAccent, size: 22),
                          tooltip: "ADD PACKAGE",
                          style: IconButton.styleFrom(
                            backgroundColor: Colors.amberAccent.withOpacity(0.1),
                            padding: const EdgeInsets.all(10),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.amberAccent.withOpacity(0.2)))
                          ),
                        ),
                      ],
                    ],
                  ),
                ),

                _buildKpiSection(provider),

                const TabBar(
                  dividerColor: Colors.transparent,
                  indicatorColor: AppColors.accent,
                  indicatorWeight: 3,
                  labelStyle: TextStyle(fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1.5),
                  unselectedLabelStyle: TextStyle(fontWeight: FontWeight.bold, fontSize: 10, letterSpacing: 1.5),
                  tabs: [
                    Tab(text: "UNITS"),
                    Tab(text: "TYPES"),
                    Tab(text: "OFFERS"),
                    Tab(text: "NEW PKG"),
                  ],
                ),

                Expanded(
                  child: provider.isLoading && provider.rooms.isEmpty
                      ? const ListSkeleton()
                      : TabBarView(
                          children: [
                            // ── TAB 1: Physical Inventory ──────────────────
                            RefreshIndicator(
                              backgroundColor: AppColors.onyx,
                              color: AppColors.accent,
                              onRefresh: () async => await provider.fetchRooms(),
                              child: CustomScrollView(
                                physics: const BouncingScrollPhysics(),
                                slivers: [
                                  SliverPadding(
                                    padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                                    sliver: SliverToBoxAdapter(
                                      child: Row(
                                        children: [
                                          const Text("LIVE INVENTORY", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Colors.white54, letterSpacing: 1)),
                                          const Spacer(),
                                          Text("${rooms.length} UNITS", style: TextStyle(fontSize: 9, color: Colors.white24, fontWeight: FontWeight.bold)),
                                        ],
                                      ),
                                    ),
                                  ),
                                  if (rooms.isEmpty)
                                    SliverFillRemaining(child: _buildEmptyState())
                                  else
                                    SliverList(
                                      delegate: SliverChildBuilderDelegate(
                                        (context, index) {
                                          final room = rooms[index];
                                          return Padding(
                                            padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                                            child: _buildRoomCard(room, _getRoomStatusColor(room.status)),
                                          );
                                        },
                                        childCount: rooms.length,
                                      ),
                                    ),
                                  const SliverToBoxAdapter(child: SizedBox(height: 80)),
                                ],
                              ),
                            ),

                            // ── TAB 2: Room Type Configuration ─────────────
                            RefreshIndicator(
                              backgroundColor: AppColors.onyx,
                              color: AppColors.accent,
                              onRefresh: () async => await provider.fetchRoomTypes(),
                              child: CustomScrollView(
                                physics: const BouncingScrollPhysics(),
                                slivers: [
                                  SliverPadding(
                                    padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                                    sliver: SliverToBoxAdapter(
                                      child: Row(
                                        children: [
                                          const Text("CONFIGURATION", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Colors.white54, letterSpacing: 1)),
                                          const Spacer(),
                                          Text("${provider.roomTypes.length} DEFINITIONS", style: TextStyle(fontSize: 9, color: Colors.white24, fontWeight: FontWeight.bold)),
                                        ],
                                      ),
                                    ),
                                  ),
                                  if (provider.roomTypes.isEmpty)
                                    SliverFillRemaining(
                                      child: Center(
                                        child: Text("NO TYPES DEFINED", style: TextStyle(color: Colors.white24, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1.5)),
                                      ),
                                    )
                                  else
                                    SliverList(
                                      delegate: SliverChildBuilderDelegate(
                                        (context, index) {
                                          final rt = provider.roomTypes[index];
                                          return Padding(
                                            padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
                                            child: _buildRoomTypeCard(rt),
                                          );
                                        },
                                        childCount: provider.roomTypes.length,
                                      ),
                                    ),
                                  const SliverToBoxAdapter(child: SizedBox(height: 80)),
                                ],
                              ),
                            ),

                            // ── TAB 3: Package Management ──────────────────
                            const _PackageManagerTab(),

                            // ── TAB 4: Create Package ──────────────────────
                            const _PackageCreateTab(),
                          ],
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

  Widget _buildRoomCard(Room room, Color statusColor) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: InkWell(
          onTap: () => _showRoomDetails(room),
          borderRadius: BorderRadius.circular(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Image Header
              if (room.imageUrl != null)
                Container(
                  height: 160,
                  decoration: BoxDecoration(
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                    image: DecorationImage(
                      image: NetworkImage(ApiConstants.imageBaseUrl + room.imageUrl!),
                      fit: BoxFit.cover,
                    ),
                  ),
                  child: Stack(
                    children: [
                      // Gradient overlay
                      Container(
                        decoration: BoxDecoration(
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                          gradient: LinearGradient(
                            begin: Alignment.topCenter,
                            end: Alignment.bottomCenter,
                            colors: [Colors.transparent, AppColors.onyx.withOpacity(0.8)],
                            stops: const [0.4, 1.0],
                          ),
                        ),
                      ),
                      // Status Badge
                      Positioned(
                        top: 12,
                        right: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: statusColor,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            room.status.toUpperCase(),
                            style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: AppColors.onyx),
                          ),
                        ),
                      ),
                      // Room Number
                      Positioned(
                        bottom: 12,
                        left: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: Colors.white24),
                          ),
                          child: Text(
                            room.roomNumber,
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              
              // Fallback if no image
              if (room.imageUrl == null)
                 Container(
                    height: 80,
                    decoration: BoxDecoration(
                       color: statusColor.withOpacity(0.1),
                       borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                    ),
                    child: Center(
                       child: Text(room.roomNumber, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: statusColor))
                    )
                 ),

              // Details Section
              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                room.type.toUpperCase(),
                                style: const TextStyle(fontWeight: FontWeight.w900, color: Colors.white, fontSize: 13, letterSpacing: 0.5),
                              ),
                              const SizedBox(height: 4),
                              Row(
                                children: [
                                  Icon(Icons.person_outline, size: 12, color: Colors.white.withOpacity(0.5)),
                                  const SizedBox(width: 4),
                                  Text(
                                    "MAX: ${room.adultsCapacity} ADULTS",
                                    style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.5), fontWeight: FontWeight.bold),
                                  ),
                                  if (room.floor > 0) ...[
                                    const SizedBox(width: 12),
                                    Icon(Icons.layers_outlined, size: 12, color: Colors.white.withOpacity(0.5)),
                                    const SizedBox(width: 4),
                                    Text(
                                      "FLOOR ${room.floor}",
                                      style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.5), fontWeight: FontWeight.bold),
                                    ),
                                  ],
                                ],
                              ),
                            ],
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(room.price),
                              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: Colors.greenAccent),
                            ),
                            const SizedBox(height: 4),
                            Text("PER NIGHT", style: TextStyle(fontSize: 8, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900)),
                          ],
                        ),
                      ],
                    ),
                    if (room.guestName != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.accent.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppColors.accent.withOpacity(0.2)),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.person, size: 12, color: AppColors.accent),
                            const SizedBox(width: 6),
                            Text(
                              room.guestName!.toUpperCase(),
                              style: TextStyle(fontSize: 10, color: AppColors.accent, fontWeight: FontWeight.w900, letterSpacing: 0.5),
                            ),
                          ],
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
                    // Amenities
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          if (room.wifi) _buildAmenityIcon(Icons.wifi, "WIFI"),
                          if (room.airConditioning) _buildAmenityIcon(Icons.ac_unit, "A/C"),
                          if (room.tv) _buildAmenityIcon(Icons.tv, "TV"),
                          if (room.miniBar) _buildAmenityIcon(Icons.kitchen, "MINI BAR"),
                          if (room.roomService) _buildAmenityIcon(Icons.room_service, "SERVICE"),
                          if (room.balcony) _buildAmenityIcon(Icons.balcony, "BALCONY"),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Actions
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        IconButton(
                          icon: Icon(Icons.edit_outlined, size: 18, color: widget.isClockedIn ? Colors.white54 : Colors.white10),
                          onPressed: widget.isClockedIn ? () => _showRoomForm(room: room) : null,
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                        const SizedBox(width: 16),
                        IconButton(
                          icon: Icon(Icons.delete_outline, size: 18, color: widget.isClockedIn ? Colors.redAccent.withOpacity(0.6) : Colors.white10),
                          onPressed: widget.isClockedIn ? () => _confirmDelete(room.id, room.roomNumber) : null,
                          padding: EdgeInsets.zero,
                          constraints: const BoxConstraints(),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAmenityIcon(IconData icon, String label) {
    return Container(
      margin: const EdgeInsets.only(right: 12),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 14, color: Colors.white.withOpacity(0.7)),
          ),
          const SizedBox(height: 4),
          Text(label, style: TextStyle(fontSize: 7, color: Colors.white.withOpacity(0.5), fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildRoomTypeCard(RoomType rt) {
    return Container(
      margin: const EdgeInsets.only(bottom: 24),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: InkWell(
          onTap: () => _showRoomTypeDetails(rt),
          borderRadius: BorderRadius.circular(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Hero Image with Stats Overlay
              Stack(
                children: [
                  if (rt.imageUrl != null)
                    _buildHeroImage(ApiConstants.imageBaseUrl + rt.imageUrl!)
                  else
                    Container(height: 180, color: Colors.white.withOpacity(0.05), child: const Center(child: Icon(Icons.broken_image, color: Colors.white10))),
                  
                  // Top Badges
                  Positioned(
                    top: 12, left: 12,
                    child: _buildCapacityChip(Icons.person, "MAX ADULTS: ${rt.adultsCapacity}", Colors.white),
                  ),
                  Positioned(
                    top: 12, right: 12,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(color: Colors.blueAccent.withOpacity(0.9), borderRadius: BorderRadius.circular(8)),
                      child: Text("${rt.totalInventory} UNITS", style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: Colors.white)),
                    ),
                  ),
                ],
              ),

              Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(rt.name.toUpperCase(), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1)),
                        ),
                        Text(NumberFormat.currency(symbol: "₹", decimalDigits: 0).format(rt.basePrice), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white)),
                      ],
                    ),
                    Text("ORCHID PREMIUM ROOM TYPE", style: TextStyle(fontSize: 8, color: Colors.blueAccent.withOpacity(0.7), fontWeight: FontWeight.w900, letterSpacing: 1.5)),
                    
                    const SizedBox(height: 12),
                    Text(
                      "Experience ultimate comfort and luxury in our meticulously designed Orchid resort rooms.",
                      style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.5), height: 1.5),
                    ),

                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Container(width: 2, height: 10, color: Colors.blueAccent),
                        const SizedBox(width: 8),
                        const Text("CORE AMENITIES", style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: Colors.white30, letterSpacing: 1)),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 16,
                      children: [
                        if (rt.wifi) _buildSmallIcon(Icons.wifi, "WIFI"),
                        if (rt.parking) _buildSmallIcon(Icons.local_parking, "PARKING"),
                        if (rt.breakfast) _buildSmallIcon(Icons.restaurant, "BREAKFAST"),
                      ],
                    ),

                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: widget.isClockedIn ? () => _showRoomTypeDialog(roomType: rt) : null,
                            icon: const Icon(Icons.edit_outlined, size: 14),
                            label: const Text("EDIT TYPE", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900)),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                              side: BorderSide(color: Colors.white.withOpacity(0.1)),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: widget.isClockedIn ? () => _deleteRoomType(rt.id, rt.name) : null,
                            icon: const Icon(Icons.delete_outline, size: 14),
                            label: const Text("DELETE", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900)),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.redAccent.withOpacity(0.7),
                              side: BorderSide(color: Colors.redAccent.withOpacity(0.2)),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                              padding: const EdgeInsets.symmetric(vertical: 12),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeroImage(String url) {
    return Container(
      height: 180,
      width: double.infinity,
      decoration: BoxDecoration(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        image: DecorationImage(image: NetworkImage(url), fit: BoxFit.cover),
      ),
      child: Container(decoration: BoxDecoration(gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Colors.transparent, AppColors.onyx.withOpacity(0.8)]))),
    );
  }

  Widget _buildSmallIcon(IconData icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 12, color: Colors.blueAccent),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 8, fontWeight: FontWeight.w900, color: Colors.white54, letterSpacing: 1)),
      ],
    );
  }

  Widget _buildCapacityChip(IconData icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white24),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 10, color: color),
          const SizedBox(width: 4),
          Text(label, style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: Colors.white)),
        ],
      ),
    );
  }

  void _showRoomTypeDetails(RoomType rt) {
    final provider = context.read<RoomProvider>();
    final typeRooms = provider.rooms.where((r) => r.roomTypeId == rt.id).toList();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.onyx.withOpacity(0.9),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
            ),
            child: DefaultTabController(
              length: 3,
              child: Column(
                children: [
                  // Header
                  Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Center(
                          child: Container(
                            width: 40, height: 4,
                            margin: const EdgeInsets.only(bottom: 24),
                            decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)),
                          ),
                        ),
                        Row(
                          children: [
                            Container(
                              width: 64, height: 64,
                              decoration: BoxDecoration(
                                color: Colors.blueAccent.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.blueAccent.withOpacity(0.2)),
                              ),
                              child: const Icon(Icons.category_rounded, color: Colors.blueAccent, size: 32),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(rt.name.toUpperCase(), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white)),
                                  Text("${rt.totalInventory} UNITS CONFIGURED", style: TextStyle(fontSize: 11, color: Colors.blueAccent.withOpacity(0.7), fontWeight: FontWeight.bold, letterSpacing: 1)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  // Image Gallery Section
                  if (rt.imageUrl != null || rt.extraImages.isNotEmpty) ...[
                    SizedBox(
                      height: 140,
                      child: ListView(
                        scrollDirection: Axis.horizontal,
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        children: [
                          if (rt.imageUrl != null)
                            _buildGalleryImage(ApiConstants.imageBaseUrl + rt.imageUrl!),
                          ...rt.extraImages.map((img) => _buildGalleryImage(ApiConstants.imageBaseUrl + img)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],

                  // Tab Bar
                  Container(
                    margin: const EdgeInsets.symmetric(horizontal: 24),
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: TabBar(
                      dividerColor: Colors.transparent,
                      indicator: BoxDecoration(
                        color: AppColors.accent,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      labelColor: AppColors.onyx,
                      unselectedLabelColor: Colors.white54,
                      labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1),
                      tabs: const [
                        Tab(text: "PRICING"),
                        Tab(text: "INVENTORY"),
                        Tab(text: "STATS"),
                      ],
                    ),
                  ),

                  Expanded(
                    child: TabBarView(
                      children: [
                        // PRICING TAB
                        ListView(
                          padding: const EdgeInsets.all(24),
                          children: [
                            _buildGlassDetailRow("WEEKDAY (BASE)", NumberFormat.currency(symbol: "₹").format(rt.basePrice), const Color(0xFF00C853)),
                            _buildGlassDetailRow("WEEKEND", rt.weekendPrice != null ? NumberFormat.currency(symbol: "₹").format(rt.weekendPrice) : "NOT SET", Colors.orangeAccent),
                            _buildGlassDetailRow("LONG WEEKEND", rt.longWeekendPrice != null ? NumberFormat.currency(symbol: "₹").format(rt.longWeekendPrice) : "NOT SET", Colors.blueAccent),
                            _buildGlassDetailRow("HOLIDAY", rt.holidayPrice != null ? NumberFormat.currency(symbol: "₹").format(rt.holidayPrice) : "NOT SET", Colors.redAccent),
                            
                            const SizedBox(height: 16),
                            _buildAmenitiesSection(rt),
                          ],
                        ),

                        // INVENTORY TAB
                        ListView.builder(
                          padding: const EdgeInsets.all(24),
                          itemCount: typeRooms.length,
                          itemBuilder: (context, index) {
                            final r = typeRooms[index];
                            return Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.white.withOpacity(0.03),
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: Colors.white.withOpacity(0.05)),
                              ),
                              child: Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                    decoration: BoxDecoration(color: _getRoomStatusColor(r.status).withOpacity(0.15), borderRadius: BorderRadius.circular(8)),
                                    child: Text(r.roomNumber, style: TextStyle(fontWeight: FontWeight.w900, color: _getRoomStatusColor(r.status))),
                                  ),
                                  const SizedBox(width: 16),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text("FLOOR ${r.floor}", style: const TextStyle(color: Colors.white54, fontSize: 10, fontWeight: FontWeight.bold)),
                                      Text(r.status.toUpperCase(), style: TextStyle(color: _getRoomStatusColor(r.status), fontSize: 10, fontWeight: FontWeight.w900)),
                                    ],
                                  ),
                                  const Spacer(),
                                  const Icon(Icons.arrow_forward_ios, size: 12, color: Colors.white12),
                                ],
                              ),
                            );
                          },
                        ),

                        // STATS TAB (Short Booking Report)
                        ListView(
                          padding: const EdgeInsets.all(24),
                          children: [
                            _buildStatCard("CURRENT OCCUPANCY", "${typeRooms.where((r) => r.status == 'Occupied').length} / ${rt.totalInventory}", Icons.pie_chart_outline, Colors.blueAccent),
                            _buildStatCard("MAINTENANCE UNITS", "${typeRooms.where((r) => r.status == 'Maintenance').length}", Icons.build_circle_outlined, Colors.redAccent),
                            _buildStatCard("REVENUE ESTIMATE (TODAY)", NumberFormat.currency(symbol: "₹").format(typeRooms.where((r) => r.status == 'Occupied').length * rt.basePrice), Icons.payments_outlined, Colors.greenAccent),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [color.withOpacity(0.1), color.withOpacity(0.05)]),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.1)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 20),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white.withOpacity(0.4), letterSpacing: 1)),
              const SizedBox(height: 4),
              Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white)),
            ],
          ),
        ],
      ),
    );
  }

  void _deleteRoomType(int id, String name) {
    showDialog(
      context: context,
      builder: (ctx) => OnyxGlassDialog(
        title: "DELETE ROOM TYPE",
        children: [
          Text(
            "ARE YOU SURE YOU WANT TO DELETE THE \"${name.toUpperCase()}\" TYPE?\nALL ASSOCIATED ROOMS MUST BE REASSIGNED FIRST.",
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11, fontWeight: FontWeight.bold),
          ),
        ],
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text("CANCEL", style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold, fontSize: 11, letterSpacing: 1)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              final api = context.read<ApiService>();
              try {
                await api.dio.delete("/rooms/types/$id");
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ROOM TYPE DELETED")));
                  Provider.of<RoomProvider>(context, listen: false).fetchRoomTypes();
                }
              } catch (e) {
                if (mounted) ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text("DELETE FAILED: $e"), backgroundColor: Colors.redAccent));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
            child: const Text("DELETE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11)),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
     return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.meeting_room_outlined, size: 64, color: Colors.white10),
          const SizedBox(height: 16),
          Text("NO UNITS FOUND", style: TextStyle(color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 11)),
        ],
      ),
    );
  }

  Color _getRoomStatusColor(String status) {
    switch (status.toLowerCase()) {
      case 'available':
      case 'clean':
      case 'ready':
        return Colors.greenAccent;
      case 'occupied':
        return Colors.blueAccent;
      case 'maintenance':
      case 'dirty':
        return Colors.redAccent;
      case 'cleaning':
        return Colors.orangeAccent;
      default:
        return Colors.white24;
    }
  }

  void _showRoomDetails(dynamic room) async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator(color: AppColors.accent)),
    );

    try {
      final api = context.read<ApiService>();
      final results = await Future.wait([
        api.dio.get('/service-requests', queryParameters: {'room_id': room.id}),
        api.dio.get('/bookings', queryParameters: {'room_id': room.id}),
      ]);

      if (!mounted) return;
      Navigator.pop(context);

      final services = results[0].data as List? ?? [];
      // /bookings returns a paginated Map: {"total": N, "bookings": [...]}
      final bookingsRaw = results[1].data;
      final List bookings = (bookingsRaw is Map && bookingsRaw['bookings'] is List)
          ? bookingsRaw['bookings'] as List
          : (bookingsRaw is List ? bookingsRaw : []);

      _displayRoomDetailsWithHistory(room, services, bookings);

    } catch (e) {
      if (!mounted) return;
      Navigator.pop(context);
      _displayRoomDetailsWithHistory(room, [], []);
    }
  }

  void _displayRoomDetailsWithHistory(dynamic room, List services, List bookings) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.9,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            decoration: BoxDecoration(
              color: AppColors.onyx.withOpacity(0.9),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
              border: Border.all(color: Colors.white.withOpacity(0.1)),
            ),
            child: DefaultTabController(
              length: 5,
              child: NestedScrollView(
                controller: scrollController,
                headerSliverBuilder: (context, innerBoxIsScrolled) => [
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Center(
                            child: Container(
                              width: 40, height: 4,
                              margin: const EdgeInsets.only(bottom: 24),
                              decoration: BoxDecoration(color: Colors.white10, borderRadius: BorderRadius.circular(2)),
                            ),
                          ),
                          Row(
                            children: [
                              Container(
                                width: 72, height: 72,
                                decoration: BoxDecoration(
                                  color: _getRoomStatusColor(room.status).withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(24),
                                  border: Border.all(color: _getRoomStatusColor(room.status).withOpacity(0.3), width: 2),
                                  boxShadow: [
                                    BoxShadow(color: _getRoomStatusColor(room.status).withOpacity(0.2), blurRadius: 15, spreadRadius: -5)
                                  ]
                                ),
                                child: Center(
                                  child: Text(
                                    room.roomNumber,
                                    style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: _getRoomStatusColor(room.status)),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 20),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      room.type.toUpperCase(),
                                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 0.5),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      "FLOOR ${room.floor}".toUpperCase(),
                                      style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.bold, letterSpacing: 1),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 24),
                          
                          // Image Gallery
                          if (room.imageUrl != null || room.extraImages.isNotEmpty) ...[
                            SizedBox(
                              height: 140,
                              child: ListView(
                                physics: const BouncingScrollPhysics(),
                                scrollDirection: Axis.horizontal,
                                children: [
                                  if (room.imageUrl != null)
                                    _buildGalleryImage(ApiConstants.imageBaseUrl + room.imageUrl!),
                                  ...room.extraImages.map((img) => _buildGalleryImage(ApiConstants.imageBaseUrl + img)),
                                ],
                              ),
                            ),
                            const SizedBox(height: 24),
                          ],

                          _buildGlassDetailRow("OPERATIONAL STATUS", room.status.toUpperCase(), _getRoomStatusColor(room.status)),
                          _buildGlassDetailRow("TARIFF / NIGHT", NumberFormat.currency(symbol: "₹").format(room.price), Colors.greenAccent),
                          
                          const SizedBox(height: 16),
                          _buildAmenitiesSection(room),

                          if (room.status != 'Occupied') ...[
                            const SizedBox(height: 16),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                              children: [
                                _buildStatusActionChip(room, "Available", Colors.greenAccent),
                                _buildStatusActionChip(room, "Cleaning", Colors.orangeAccent),
                                _buildStatusActionChip(room, "Maintenance", Colors.redAccent),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                  SliverPersistentHeader(
                    pinned: true,
                    delegate: _SliverAppBarDelegate(
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                        decoration: BoxDecoration(
                          color: AppColors.onyx.withOpacity(0.95),
                        ),
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: Colors.white.withOpacity(0.05))
                          ),
                          child: TabBar(
                            labelColor: AppColors.onyx,
                            unselectedLabelColor: Colors.white.withOpacity(0.7),
                            indicatorSize: TabBarIndicatorSize.tab,
                            indicator: BoxDecoration(
                              borderRadius: BorderRadius.circular(16),
                              color: AppColors.accent,
                            ),
                            dividerColor: Colors.transparent,
                            labelStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 9, letterSpacing: 1),
                            tabs: const [
                              Tab(text: "SERVICES"),
                              Tab(text: "STOCKS"),
                              Tab(text: "INVENTORY"),
                              Tab(text: "GUESTS"),
                              Tab(text: "LOG"),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
                body: Column(
                  children: [
                    Expanded(
                      child: TabBarView(
                        physics: const BouncingScrollPhysics(),
                        children: [
                          _buildServicesTab(services),
                          _RoomInventoryTab(roomId: room.id),
                          _RoomPhysicalItemsTab(inventoryLocationId: room.inventoryLocationId),
                          _buildGuestsTab(bookings),
                          _RoomActivityTab(roomId: room.id),
                        ],
                      ),
                    ),
                    // Action Buttons
                    Padding(
                      padding: const EdgeInsets.all(24),
                      child: Row(
                        children: [
                          Expanded(
                            child: ElevatedButton(
                              onPressed: widget.isClockedIn ? () { Navigator.pop(context); _showRoomForm(room: room); } : null,
                              style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), padding: const EdgeInsets.symmetric(vertical: 16), elevation: 0),
                              child: const Text("EDIT UNIT", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1.5)),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: OutlinedButton(
                              onPressed: widget.isClockedIn ? () { Navigator.pop(context); _confirmDelete(room.id, room.roomNumber); } : null,
                              style: OutlinedButton.styleFrom(foregroundColor: Colors.redAccent, side: const BorderSide(color: Colors.redAccent, width: 0.5), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)), padding: const EdgeInsets.symmetric(vertical: 16)),
                              child: const Text("DELETE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1.5)),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),

          ),
        ),
      ),
    );
  }

  Widget _buildGlassDetailRow(String label, String value, Color color) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03), 
        borderRadius: BorderRadius.circular(16), 
        border: Border.all(color: Colors.white.withOpacity(0.05))
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1.2)),
          Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: color)),
        ],
      ),
    );
  }

  Widget _buildAmenitiesSection(dynamic room) {
    final List<Map<String, dynamic>> items = [
      {'icon': Icons.person, 'label': '${room.adultsCapacity} ADULTS', 'show': true},
      if (room.childrenCapacity > 0) {'icon': Icons.child_care, 'label': '${room.childrenCapacity} CHILD', 'show': true},
      {'icon': Icons.ac_unit, 'label': 'A/C', 'show': room.airConditioning},
      {'icon': Icons.wifi, 'label': 'WIFI', 'show': room.wifi},
      {'icon': Icons.tv, 'label': 'TV', 'show': room.tv},
      {'icon': Icons.kitchen, 'label': 'MINI BAR', 'show': room.miniBar},
      {'icon': Icons.room_service, 'label': 'SERVICE', 'show': room.roomService},
      {'icon': Icons.balcony, 'label': 'BALCONY', 'show': room.balcony},
      {'icon': Icons.pool, 'label': 'POOL', 'show': room.privatePool},
      {'icon': Icons.fitness_center, 'label': 'GYM', 'show': room.gymAccess},
      {'icon': Icons.spa, 'label': 'SPA', 'show': room.spaAccess},
    ];

    final activeItems = items.where((i) => i['show'] == true).toList();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(width: 2, height: 12, color: AppColors.accent),
            const SizedBox(width: 8),
            Text("UNIT FEATURES", style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w900, letterSpacing: 1.2)),
          ],
        ),
        const SizedBox(height: 16),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: activeItems.map((item) => Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.02),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white.withOpacity(0.05)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(item['icon'] as IconData, size: 14, color: AppColors.accent),
                const SizedBox(width: 8),
                Text(
                  (item['label'] as String).toUpperCase(),
                  style: const TextStyle(fontSize: 9, color: Colors.white70, fontWeight: FontWeight.bold, letterSpacing: 0.5),
                ),
              ],
            ),
          )).toList(),
        ),
      ],
    );
  }

  Widget _buildGalleryImage(String url) {
    return Container(
      width: 180,
      margin: const EdgeInsets.only(right: 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white10),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Image.network(
          url,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => Container(
            color: Colors.white.withOpacity(0.05),
            child: const Center(child: Icon(Icons.broken_image, color: Colors.white10)),
          ),
        ),
      ),
    );
  }

  Widget _buildStatusActionChip(dynamic room, String status, Color color) {
     final isSelected = room.status == status;
     return InkWell(
       onTap: () {
         if (!isSelected) _quickUpdateStatus(room, status);
       },
       borderRadius: BorderRadius.circular(12),
       child: Container(
         padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
         decoration: BoxDecoration(
           color: isSelected ? color : Colors.white.withOpacity(0.05),
           borderRadius: BorderRadius.circular(12),
           border: Border.all(color: isSelected ? color : Colors.white10),
           boxShadow: isSelected ? [BoxShadow(color: color.withOpacity(0.3), blurRadius: 8, offset: const Offset(0, 2))] : null,
         ),
         child: Text(
           status.toUpperCase(),
           style: TextStyle(
             color: isSelected ? AppColors.onyx : Colors.white.withOpacity(0.6),
             fontSize: 9,
             fontWeight: FontWeight.w900,
             letterSpacing: 1,
           ),
         ),
       ),
     );
  }

  Future<void> _quickUpdateStatus(dynamic room, String newStatus) async {
      Navigator.pop(context);
      final api = context.read<ApiService>();
      try {
         await api.updateRoom(room.id, {'status': newStatus});
         if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("UNIT STATUS UPDATED: ${newStatus.toUpperCase()}"), backgroundColor: _getRoomStatusColor(newStatus)));
            context.read<RoomProvider>().fetchRooms();
         }
      } catch (e) {
          if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("UPDATE FAILED: $e"), backgroundColor: Colors.redAccent));
      }
  }

  Widget _buildServicesTab(List services) {
    if (services.isEmpty) {
      return Center(child: Text('NO SERVICE HISTORY', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)));
    }

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      physics: const BouncingScrollPhysics(),
      itemCount: services.length,
      itemBuilder: (context, index) {
        final service = services[index];
        final status = service['status'] ?? 'pending';
        Color statusColor = Colors.orangeAccent;
        if (status == 'completed') statusColor = Colors.greenAccent;
        if (status == 'in_progress') statusColor = Colors.blueAccent;

        return Container(
          margin: const EdgeInsets.only(bottom: 20),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(20),
            borderColor: statusColor.withOpacity(0.15),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(color: statusColor.withOpacity(0.1), shape: BoxShape.circle),
                      child: Icon(
                        status == 'completed' ? Icons.check_circle_outline : Icons.room_service_outlined,
                        color: statusColor,
                        size: 18,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        (service['type'] ?? service['request_type'] ?? 'Service').toString().toUpperCase(),
                        style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15, color: Colors.white, letterSpacing: 0.5),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(color: statusColor.withOpacity(0.1), borderRadius: BorderRadius.circular(10), border: Border.all(color: statusColor.withOpacity(0.2))),
                      child: Text(status.toUpperCase(), style: TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: statusColor, letterSpacing: 1)),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                if (service['employee_name'] != null)
                  _buildServiceDetailRow('ASSIGNED', service['employee_name'].toString().toUpperCase(), Icons.person_outline),
                if (service['guest_name'] != null)
                  _buildServiceDetailRow('GUEST', service['guest_name'].toString().toUpperCase(), Icons.person),
                if (service['created_at'] != null)
                  _buildServiceDetailRow('REQUESTED', DateFormat('MMM dd, hh:mm a').format(DateTime.parse(service['created_at'])), Icons.access_time),
                if (service['completed_at'] != null)
                  _buildServiceDetailRow('COMPLETED', DateFormat('MMM dd, hh:mm a').format(DateTime.parse(service['completed_at'])), Icons.check_circle_outline),
                if (service['description'] != null && service['description'].toString().isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(service['description'].toString(), style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 12, fontStyle: FontStyle.italic)),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildServiceDetailRow(String label, String value, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Icon(icon, size: 14, color: Colors.white24),
          const SizedBox(width: 12),
          Text('$label: ', style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold, letterSpacing: 0.5)),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 0.5)),
          ),
        ],
      ),
    );
  }



  Widget _buildGuestsTab(List bookings) {
    if (bookings.isEmpty) return Center(child: Text('NO GUEST HISTORY', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)));
    return ListView.builder(
      padding: const EdgeInsets.all(24),
      itemCount: bookings.length,
      itemBuilder: (context, index) {
        final booking = bookings[index];
        final checkIn = booking['check_in'] != null ? DateTime.parse(booking['check_in']) : null;
        final checkOut = booking['check_out'] != null ? DateTime.parse(booking['check_out']) : null;
        final isActive = checkOut != null && checkOut.isAfter(DateTime.now()) && checkIn != null && checkIn.isBefore(DateTime.now());

        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          child: OnyxGlassCard(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(child: Text(booking['guest_name']?.toString().toUpperCase() ?? 'GUEST', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14, color: Colors.white, letterSpacing: 0.5))),
                    if (isActive) Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), decoration: BoxDecoration(color: Colors.greenAccent.withOpacity(0.15), borderRadius: BorderRadius.circular(8)), child: const Text('ACTIVE', style: TextStyle(fontSize: 8, fontWeight: FontWeight.w900, color: Colors.greenAccent))),
                  ],
                ),
                const SizedBox(height: 16),
                _buildServiceDetailRow('CHECK-IN', checkIn != null ? DateFormat('MMM dd, yyyy').format(checkIn) : 'N/A', Icons.login),
                _buildServiceDetailRow('CHECK-OUT', checkOut != null ? DateFormat('MMM dd, yyyy').format(checkOut) : 'N/A', Icons.logout),
                _buildServiceDetailRow('TOTAL', '₹${NumberFormat.compact().format(booking['total_amount'] ?? 0)}', Icons.payments_outlined),
              ],
            ),
          ),
        );
      },
    );
  }



  void _showRoomTypeDialog({RoomType? roomType}) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => RoomTypeFormScreen(roomType: roomType)),
    ).then((_) {
      if (mounted) Provider.of<RoomProvider>(context, listen: false).fetchRoomTypes();
    });
  }

  void _showRoomForm({Room? room}) {
    if (!widget.isClockedIn) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PLEASE CLOCK IN TO MANAGE ROOMS"), backgroundColor: Colors.redAccent));
      return;
    }
    
    final numberController = TextEditingController(text: room?.roomNumber ?? "");
    final priceController = TextEditingController(text: room?.price.toString() ?? "");
    final floorController = TextEditingController(text: room?.floor.toString() ?? "1");
    String selectedStatus = room?.status ?? "Available";
    final provider = Provider.of<RoomProvider>(context, listen: false);
    final types = provider.roomTypes;
    int? selectedRoomTypeId = room?.roomTypeId;
    
    List<XFile> newRoomImages = [];
    List<Uint8List> roomImagePreviews = [];
    
    // Auto-select room type if editing
    if (room != null && selectedRoomTypeId == null) {
      final match = types.where((t) => t.name.toLowerCase() == room.type.toLowerCase()).firstOrNull;
      if (match != null) selectedRoomTypeId = match.id;
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            decoration: BoxDecoration(color: AppColors.onyx.withOpacity(0.95), borderRadius: const BorderRadius.vertical(top: Radius.circular(32)), border: Border.all(color: Colors.white10)),
            padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom, left: 32, right: 32, top: 32),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(room == null ? "ESTABLISH NEW UNIT" : "UPDATE UNIT ${room.roomNumber}", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: 1.5)),
                  const SizedBox(height: 32),
                  _buildGlassInput(numberController, "ROOM IDENTIFIER", Icons.numbers, type: TextInputType.text),
                  const SizedBox(height: 16),
                  
                  _buildGlassDropdown<int>(
                    label: "CATEGORIZATION",
                    value: selectedRoomTypeId,
                    items: types.map((t) => DropdownMenuItem(
                      value: t.id,
                      child: Text(t.name.toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    )).toList(),
                    onChanged: (val) {
                      setModalState(() {
                        selectedRoomTypeId = val;
                        if (room == null && val != null) {
                          final type = types.firstWhere((t) => t.id == val);
                          priceController.text = type.basePrice.toString();
                        }
                      });
                    },
                  ),
                  
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(child: _buildGlassInput(priceController, "VALUATION", Icons.payments_outlined, prefix: "₹", type: TextInputType.number)),
                      const SizedBox(width: 12),
                      Expanded(child: _buildGlassInput(floorController, "LEVEL / FLOOR", Icons.layers_outlined, type: TextInputType.number)),
                    ],
                  ),
                  const SizedBox(height: 16),
                   _buildGlassDropdown<String>(
                    label: "OPERATIONAL STATUS",
                    value: selectedStatus,
                    items: ["Available", "Occupied", "Maintenance", "Cleaning"].map((s) => DropdownMenuItem(
                      value: s, 
                      child: Text(s.toUpperCase(), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold))
                    )).toList(),
                    onChanged: (val) => setModalState(() => selectedStatus = val!),
                  ),
                  const SizedBox(height: 24),
                  const Text("ROOM IMAGES", style: TextStyle(color: Colors.white60, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
                  const SizedBox(height: 12),
                  Container(
                    height: 100,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: [
                        InkWell(
                          onTap: () async {
                            final picker = ImagePicker();
                            final images = await picker.pickMultiImage();
                            if (images.isNotEmpty) {
                              for (var img in images) {
                                final bytes = await img.readAsBytes();
                                setModalState(() {
                                  newRoomImages.add(img);
                                  roomImagePreviews.add(bytes);
                                });
                              }
                            }
                          },
                          child: Container(
                            width: 100,
                            decoration: BoxDecoration(
                              color: Colors.white.withOpacity(0.05),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: Colors.white10),
                            ),
                            child: const Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.add_a_photo_outlined, color: AppColors.accent, size: 24),
                                SizedBox(height: 4),
                                Text("ADD", style: TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900)),
                              ],
                            ),
                          ),
                        ),
                        ...roomImagePreviews.asMap().entries.map((e) => Container(
                          width: 100,
                          margin: const EdgeInsets.only(left: 12),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(16),
                            image: DecorationImage(image: MemoryImage(e.value), fit: BoxFit.cover),
                            border: Border.all(color: Colors.white10),
                          ),
                          child: Stack(
                            children: [
                              Positioned(
                                top: 4, right: 4,
                                child: InkWell(
                                  onTap: () => setModalState(() {
                                    newRoomImages.removeAt(e.key);
                                    roomImagePreviews.removeAt(e.key);
                                  }),
                                  child: Container(
                                    padding: const EdgeInsets.all(4),
                                    decoration: const BoxDecoration(color: Colors.black54, shape: BoxShape.circle),
                                    child: const Icon(Icons.close, color: Colors.white, size: 12),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        )),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),
                  SizedBox(
                    width: double.infinity, 
                    height: 56,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.accent, 
                        foregroundColor: AppColors.onyx, 
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        elevation: 0,
                      ),
                      onPressed: () async {
                        if (selectedRoomTypeId == null || numberController.text.isEmpty) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("FIELDS CANNOT BE VACANT")));
                          return;
                        }
                        
                        final api = Provider.of<ApiService>(context, listen: false);
                        Navigator.pop(ctx);
                        
                        try {
                          final formDataMap = {
                            "number": numberController.text,
                            "room_type_id": selectedRoomTypeId,
                            "status": selectedStatus,
                            "floor": int.tryParse(floorController.text) ?? 1,
                            "price": double.tryParse(priceController.text) ?? 0.0,
                          };

                          final formData = FormData.fromMap(formDataMap);
                          for (var img in newRoomImages) {
                            formData.files.add(MapEntry(
                              "images",
                              await MultipartFile.fromBytes(await img.readAsBytes(), filename: img.name),
                            ));
                          }

                          if (room == null) {
                            await api.dio.post("/rooms", data: formData);
                          } else {
                            await api.dio.put("/rooms/${room.id}", data: formData);
                          }

                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("ROOM REGISTRY UPDATED")));
                            Provider.of<RoomProvider>(context, listen: false).fetchRooms();
                          }
                        } catch (e) {
                          if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("REGISTRY ERROR: $e"), backgroundColor: Colors.redAccent));
                        }
                      },
                      child: Text(room == null ? "ADD TO REGISTRY" : "UPDATE REGISTRY", style: const TextStyle(fontWeight: FontWeight.w900, letterSpacing: 2)),
                    ),
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _confirmDelete(int id, String number) {
    showDialog(
      context: context,
      builder: (ctx) => OnyxGlassDialog(
          title: "DELETE UNIT",
          children: [
              Text(
                "ARE YOU SURE YOU WANT TO REMOVE UNIT $number FROM THE REPOSITORY?",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11, fontWeight: FontWeight.bold),
              ),
          ],
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: Text("CANCEL", style: TextStyle(color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.bold, fontSize: 11, letterSpacing: 1))),
            ElevatedButton(
              onPressed: () async {
                Navigator.pop(ctx);
                final api = context.read<ApiService>();
                try {
                  await api.deleteRoom(id);
                  if (mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("UNIT DELETED SUCCESSFULLY")));
                    context.read<RoomProvider>().fetchRooms();
                  }
                } catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("DELETE FAILED: $e"), backgroundColor: Colors.redAccent)); }
              },
              style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent, foregroundColor: Colors.white),
              child: const Text("DELETE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 11)),
            ),
          ],
        ),
    );
  }

  PopupMenuItem<String> _buildFilterItem(String value, String label, IconData icon, Color color) {
    return PopupMenuItem(
      value: value,
      child: Row(
        children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 12),
          Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1)),
        ],
      ),
    );
  }

  Widget _buildGlassInput(TextEditingController controller, String label, IconData icon, {TextInputType type = TextInputType.text, String? prefix}) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: TextField(
        controller: controller,
        keyboardType: type,
        style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
          prefixIcon: Icon(icon, color: AppColors.accent, size: 18),
          prefixText: prefix,
          prefixStyle: const TextStyle(color: AppColors.accent),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        ),
      ),
    );
  }

  Widget _buildGlassDropdown<T>({required String label, required T? value, required List<DropdownMenuItem<T>> items, required ValueChanged<T?> onChanged}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButtonFormField<T>(
          value: value,
          items: items,
          onChanged: onChanged,
          dropdownColor: AppColors.onyx.withOpacity(0.95),
          style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
          decoration: InputDecoration(
            labelText: label,
            labelStyle: TextStyle(color: Colors.white.withOpacity(0.3), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
            ),
          ),
        ),
      );
  }

  void _showPackageForm({PackageModel? package}) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _PackageFormDialog(package: package),
    );
  }

}


// ─── Inline Package Creation Tab ────────────────────────────────────────────
class _PackageCreateTab extends StatefulWidget {
  const _PackageCreateTab();

  @override
  State<_PackageCreateTab> createState() => _PackageCreateTabState();
}

class _PackageCreateTabState extends State<_PackageCreateTab> {
  final _formKey = GlobalKey<FormState>();
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  final _priceCtrl = TextEditingController();
  final _adultsCtrl = TextEditingController(text: "2");
  final _childrenCtrl = TextEditingController(text: "0");
  final _stayCtrl = TextEditingController();
  final _complimentaryCtrl = TextEditingController();
  final _themeCtrl = TextEditingController();

  String _bookingType = "room_type";
  List<int> _selectedRoomTypes = [];
  
  final Map<String, Map<String, dynamic>> _foodConfigs = {
    "Breakfast": {"enabled": false, "time": "08:00", "items": <Map<String,dynamic>>[]},
    "Lunch": {"enabled": false, "time": "13:00", "items": <Map<String,dynamic>>[]},
    "Snacks": {"enabled": false, "time": "16:00", "items": <Map<String,dynamic>>[]},
    "Dinner": {"enabled": false, "time": "20:00", "items": <Map<String,dynamic>>[]},
  };
  
  List<dynamic> _availableFoodItems = [];
  List<XFile> _images = [];
  bool _isSaving = false;

  final List<String> _suggestedThemes = ["Romance", "Adventure", "Family", "Honeymoon", "Business", "Relaxation", "Weekend Getaway"];

  @override
  void initState() {
    super.initState();
    _loadFoodItems();
  }

  Future<void> _loadFoodItems() async {
    try {
      final res = await context.read<ApiService>().getFoodItems();
      final data = res.data is List ? res.data : (res.data['items'] ?? res.data);
      if (data is List) {
        if (mounted) setState(() => _availableFoodItems = data);
      }
    } catch (e) {
      debugPrint("Error loading food items: $e");
    }
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    _priceCtrl.dispose();
    _adultsCtrl.dispose();
    _childrenCtrl.dispose();
    _stayCtrl.dispose();
    _complimentaryCtrl.dispose();
    _themeCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickImages() async {
    final picked = await ImagePicker().pickMultiImage();
    if (picked.isNotEmpty) setState(() => _images.addAll(picked));
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (_bookingType == 'room_type' && _selectedRoomTypes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PLEASE SELECT AT LEAST ONE ROOM TYPE"), backgroundColor: Colors.amberAccent));
      return;
    }
    setState(() => _isSaving = true);

    final foodTimingMap = {};
    for (var meal in _foodConfigs.keys) {
      if (_foodConfigs[meal]!['enabled'] == true) {
        foodTimingMap[meal] = {
          "time": _foodConfigs[meal]!['time'],
          "items": _foodConfigs[meal]!['items'],
        };
      }
    }

    final formData = FormData.fromMap({
      'title': _titleCtrl.text.trim(),
      'description': _descCtrl.text.trim(),
      'price': double.tryParse(_priceCtrl.text) ?? 0.0,
      'booking_type': _bookingType,
      if (_bookingType == 'room_type') 'room_types': _selectedRoomTypes.join(","),
      'default_adults': int.tryParse(_adultsCtrl.text) ?? 2,
      'default_children': int.tryParse(_childrenCtrl.text) ?? 0,
      if (_stayCtrl.text.isNotEmpty) 'max_stay_days': int.tryParse(_stayCtrl.text) ?? 1,
      'food_included': foodTimingMap.keys.join(", "),
      'food_timing': jsonEncode(foodTimingMap),
      'complimentary': _complimentaryCtrl.text.trim(),
      'theme': _themeCtrl.text.trim(),
      'status': 'active',
    });

    for (var i = 0; i < _images.length; i++) {
      formData.files.add(MapEntry(
        'images',
        await MultipartFile.fromFile(_images[i].path, filename: 'pkg_img_$i.jpg'),
      ));
    }

    try {
      final success = await context.read<PackageProvider>().createPackage(formData);
      if (!mounted) return;
      setState(() => _isSaving = false);
      if (success) {
        // Reset form
        _titleCtrl.clear(); _descCtrl.clear(); _priceCtrl.clear();
        _stayCtrl.clear(); _complimentaryCtrl.clear(); _themeCtrl.clear();
        setState(() { 
          _images = []; 
          _selectedRoomTypes = [];
          for (var v in _foodConfigs.values) { v['enabled'] = false; v['items'] = []; }
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("PACKAGE PUBLISHED SUCCESSFULLY")),
        );
        // Jump to OFFERS tab (index 2)
        DefaultTabController.of(context).animateTo(2);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("FAILED TO CREATE PACKAGE"), backgroundColor: Colors.redAccent),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("ERROR: $e"), backgroundColor: Colors.redAccent),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(24, 16, 24, 120),
        physics: const BouncingScrollPhysics(),
        children: [
          // Header
          Container(
            margin: const EdgeInsets.only(bottom: 24),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.amberAccent.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.amberAccent.withOpacity(0.2)),
                  ),
                  child: const Icon(Icons.loyalty_rounded, color: Colors.amberAccent, size: 20),
                ),
                const SizedBox(width: 12),
                const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("CREATE PACKAGE", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w900, letterSpacing: 1)),
                    Text("DEFINE A NEW RESORT OFFER", style: TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold, letterSpacing: 1)),
                  ],
                ),
              ],
            ),
          ),

          _pctField("PACKAGE NAME *", _titleCtrl, Icons.loyalty_outlined),
          _pctField("DESCRIPTION *", _descCtrl, Icons.description_outlined, maxLines: 3),
          
          _sectionLabel("THEME / TAGLINE"),
          const SizedBox(height: 6),
          Autocomplete<String>(
            optionsBuilder: (TextEditingValue textEditingValue) {
              if (textEditingValue.text == '') {
                return _suggestedThemes;
              }
              return _suggestedThemes.where((String option) {
                return option.toLowerCase().contains(textEditingValue.text.toLowerCase());
              });
            },
            onSelected: (String selection) {
              _themeCtrl.text = selection;
            },
            fieldViewBuilder: (context, textEditingController, focusNode, onFieldSubmitted) {
              if (_themeCtrl.text.isNotEmpty && textEditingController.text.isEmpty) {
                 textEditingController.text = _themeCtrl.text;
              }
              textEditingController.addListener(() {
                 _themeCtrl.text = textEditingController.text;
              });
              return TextFormField(
                controller: textEditingController,
                focusNode: focusNode,
                style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                decoration: InputDecoration(
                  prefixIcon: const Icon(Icons.palette_outlined, color: Colors.white24, size: 18),
                  filled: true,
                  fillColor: Colors.white.withOpacity(0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
                  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
                  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Colors.amberAccent, width: 1)),
                  contentPadding: const EdgeInsets.all(14),
                ),
              );
            },
            optionsViewBuilder: (context, onSelected, options) {
              return Align(
                alignment: Alignment.topLeft,
                child: Material(
                  color: AppColors.onyx,
                  elevation: 4.0,
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    width: MediaQuery.of(context).size.width - 48,
                    decoration: BoxDecoration(
                      border: Border.all(color: Colors.white10),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: ListView.builder(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      shrinkWrap: true,
                      itemCount: options.length,
                      itemBuilder: (BuildContext context, int index) {
                        final String option = options.elementAt(index);
                        return ListTile(
                          title: Text(option, style: const TextStyle(color: Colors.white, fontSize: 13)),
                          onTap: () => onSelected(option),
                        );
                      },
                    ),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 16),

          _pctField("BASE PRICE (₹) *", _priceCtrl, Icons.payments_outlined, keyboard: TextInputType.number),

          const SizedBox(height: 8),
          _sectionLabel("BOOKING SCOPE"),
          const SizedBox(height: 8),
          Row(children: [
            _scopeChip("ROOM TYPES", "room_type"),
            const SizedBox(width: 12),
            _scopeChip("ENTIRE RESORT", "resort"),
          ]),
          if (_bookingType == 'room_type') ...[
            const SizedBox(height: 16),
            _sectionLabel("SELECT ROOM TYPES *"),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.02),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white10),
              ),
              child: Consumer<RoomProvider>(
                builder: (context, provider, child) {
                  return Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: provider.roomTypes.map((rt) {
                      final isSelected = _selectedRoomTypes.contains(rt.id);
                      return GestureDetector(
                        onTap: () {
                          setState(() {
                            if (isSelected) _selectedRoomTypes.remove(rt.id);
                            else _selectedRoomTypes.add(rt.id);
                          });
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          decoration: BoxDecoration(
                            color: isSelected ? Colors.amberAccent.withOpacity(0.1) : Colors.white.withOpacity(0.04),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: isSelected ? Colors.amberAccent.withOpacity(0.4) : Colors.transparent),
                          ),
                          child: Text(rt.name.toUpperCase(), style: TextStyle(
                            color: isSelected ? Colors.amberAccent : Colors.white38,
                            fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 0.5,
                          )),
                        ),
                      );
                    }).toList(),
                  );
                },
              ),
            ),
          ],

          const SizedBox(height: 20),
          Row(children: [
            Expanded(child: _pctField("ADULTS", _adultsCtrl, Icons.person_outline, keyboard: TextInputType.number, required: false)),
            const SizedBox(width: 12),
            Expanded(child: _pctField("CHILDREN", _childrenCtrl, Icons.child_care_outlined, keyboard: TextInputType.number, required: false)),
          ]),
          _pctField("MAX STAY (DAYS)", _stayCtrl, Icons.calendar_today_outlined, keyboard: TextInputType.number, required: false),
          _pctField("INCLUSIONS / COMPLIMENTARY", _complimentaryCtrl, Icons.star_outline, maxLines: 2, required: false),

          const SizedBox(height: 8),
          _sectionLabel("FOOD INCLUDED"),
          const SizedBox(height: 8),
          ..._foodConfigs.keys.map((meal) => _buildMealConfig(meal)).toList(),

          const SizedBox(height: 24),
          _sectionLabel("GALLERY IMAGES"),
          const SizedBox(height: 12),
          SizedBox(
            height: 100,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                GestureDetector(
                  onTap: _pickImages,
                  child: Container(
                    width: 100,
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white10),
                    ),
                    child: const Icon(Icons.add_photo_alternate_outlined, color: Colors.white24),
                  ),
                ),
                ..._images.map((f) => Container(
                  width: 100,
                  margin: const EdgeInsets.only(left: 12),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: kIsWeb
                      ? Image.network(f.path, fit: BoxFit.cover)
                      : Image.file(File(f.path), fit: BoxFit.cover),
                  ),
                )),
              ],
            ),
          ),

          const SizedBox(height: 36),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isSaving ? null : _save,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.amberAccent,
                foregroundColor: AppColors.onyx,
                padding: const EdgeInsets.symmetric(vertical: 18),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                elevation: 0,
              ),
              child: _isSaving
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.onyx))
                : const Text("PUBLISH PACKAGE", style: TextStyle(fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 2)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _sectionLabel(String text) => Text(
    text,
    style: const TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
  );

  Widget _pctField(String label, TextEditingController ctrl, IconData icon, {int maxLines = 1, TextInputType? keyboard, bool required = true}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _sectionLabel(label),
          const SizedBox(height: 6),
          TextFormField(
            controller: ctrl,
            maxLines: maxLines,
            keyboardType: keyboard,
            style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: Colors.white24, size: 18),
              filled: true,
              fillColor: Colors.white.withOpacity(0.05),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
              enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide.none),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Colors.amberAccent, width: 1)),
              contentPadding: const EdgeInsets.all(14),
            ),
            validator: required ? (v) => (v == null || v.trim().isEmpty) ? "REQUIRED" : null : null,
          ),
        ],
      ),
    );
  }

  Widget _scopeChip(String label, String value) {
    final selected = _bookingType == value;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _bookingType = value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: selected ? Colors.amberAccent.withOpacity(0.1) : Colors.white.withOpacity(0.04),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: selected ? Colors.amberAccent.withOpacity(0.4) : Colors.transparent),
          ),
          child: Center(
            child: Text(label, style: TextStyle(
              color: selected ? Colors.amberAccent : Colors.white38,
              fontSize: 10, fontWeight: FontWeight.w900,
            )),
          ),
        ),
      ),
    );
  }



  Widget _buildMealConfig(String meal) {
    final config = _foodConfigs[meal]!;
    final isEnabled = config['enabled'] as bool;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        CheckboxListTile(
          title: Text(meal, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13)),
          value: isEnabled,
          onChanged: (v) => setState(() => config['enabled'] = v ?? false),
          activeColor: Colors.amberAccent,
          checkColor: AppColors.onyx,
          contentPadding: EdgeInsets.zero,
          controlAffinity: ListTileControlAffinity.leading,
          visualDensity: VisualDensity.compact,
        ),
        if (isEnabled)
          Container(
            padding: const EdgeInsets.all(16),
            margin: const EdgeInsets.only(bottom: 16, left: 12, right: 12),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.03),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.access_time, color: Colors.white38, size: 14),
                    const SizedBox(width: 8),
                    const Text("SCHEDULE TIME", style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900)),
                    const Spacer(),
                    GestureDetector(
                      onTap: () async {
                        final timeParts = config['time'].split(':');
                        final initialTime = TimeOfDay(hour: int.parse(timeParts[0]), minute: int.parse(timeParts[1]));
                        final picked = await showTimePicker(context: context, initialTime: initialTime);
                        if (picked != null) {
                          setState(() => config['time'] = "${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')}");
                        }
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.amberAccent.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.amberAccent.withOpacity(0.3)),
                        ),
                        child: Text(config['time'], style: const TextStyle(color: Colors.amberAccent, fontWeight: FontWeight.bold, fontSize: 12)),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                const Text("SPECIFIC FOOD ITEMS (COMPLIMENTARY)", style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900)),
                const SizedBox(height: 8),
                if ((config['items'] as List).isEmpty)
                  const Padding(
                    padding: EdgeInsets.only(bottom: 8.0),
                    child: Text("No specific items selected (All available)", style: TextStyle(color: Colors.white24, fontSize: 10, fontStyle: FontStyle.italic)),
                  ),
                ...(config['items'] as List).asMap().entries.map((entry) {
                  final idx = entry.key;
                  final itemData = entry.value;
                  final foodItem = _availableFoodItems.firstWhere((f) => f['id'] == itemData['id'], orElse: () => null);
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8.0),
                    child: Row(
                      children: [
                        Expanded(child: Text(foodItem?['name'] ?? "Unknown Item", style: const TextStyle(color: Colors.white, fontSize: 12))),
                        Text("Qty: ${itemData['qty']}", style: const TextStyle(color: Colors.white54, fontSize: 10)),
                        const SizedBox(width: 8),
                        GestureDetector(
                          onTap: () => setState(() => (config['items'] as List).removeAt(idx)),
                          child: const Icon(Icons.close, color: Colors.redAccent, size: 16),
                        ),
                      ],
                    ),
                  );
                }).toList(),
                const SizedBox(height: 8),
                DropdownButtonHideUnderline(
                  child: DropdownButton<int>(
                    hint: const Text("+ Add Food Item", style: TextStyle(color: Colors.amberAccent, fontSize: 11, fontWeight: FontWeight.bold)),
                    dropdownColor: AppColors.onyx,
                    isExpanded: true,
                    icon: const Icon(Icons.keyboard_arrow_down, color: Colors.amberAccent, size: 16),
                    items: _availableFoodItems.map((f) => DropdownMenuItem<int>(
                      value: f['id'] as int,
                      child: Text(f['name'], style: const TextStyle(color: Colors.white, fontSize: 12)),
                    )).toList(),
                    onChanged: (val) {
                      if (val != null) {
                        setState(() {
                          (config['items'] as List).add({"id": val, "qty": 1});
                        });
                      }
                    },
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _RoomInventoryTab extends StatefulWidget {
  final int roomId;
  const _RoomInventoryTab({required this.roomId});

  @override
  State<_RoomInventoryTab> createState() => _RoomInventoryTabState();
}

class _RoomInventoryTabState extends State<_RoomInventoryTab> {
  late Future<Response> _inventoryFuture;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  void _refresh() {
    _inventoryFuture = context.read<ApiService>().dio.get('/rooms/${widget.roomId}/inventory-usage');
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Response>(
      future: _inventoryFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator(color: AppColors.accent));
        if (snapshot.hasError) {
          return Center(child: Text('ERROR LOADING STOCKS', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)));
        }
        final items = snapshot.data?.data as List? ?? [];
        if (items.isEmpty) return Center(child: Text('NO INVENTORY USAGE', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)));
        
        return ListView.builder(
          padding: const EdgeInsets.all(24),
          itemCount: items.length,
          itemBuilder: (context, index) {
            final item = items[index];
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: OnyxGlassCard(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), shape: BoxShape.circle),
                      child: Icon(Icons.inventory_2_outlined, color: AppColors.accent, size: 18),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item['item_name']?.toString().toUpperCase() ?? "UNKNOWN ITEM", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 12)),
                          Text("${item['quantity']} UNITS CONSUMED", style: TextStyle(color: Colors.white54, fontSize: 10, fontWeight: FontWeight.bold)),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(item['used_by_name']?.toString().toUpperCase() ?? "SYSTEM", style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 9)),
                        Text(item['used_at'] != null ? DateFormat('MMM d, hh:mm a').format(DateTime.parse(item['used_at'])) : "N/A", style: TextStyle(color: Colors.white24, fontSize: 8)),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _RoomActivityTab extends StatefulWidget {
  final int roomId;
  const _RoomActivityTab({required this.roomId});

  @override
  State<_RoomActivityTab> createState() => _RoomActivityTabState();
}

class _RoomActivityTabState extends State<_RoomActivityTab> {
  late Future<Response> _activityFuture;

  @override
  void initState() {
    super.initState();
    _activityFuture = context.read<ApiService>().dio.get('/rooms/${widget.roomId}/activity-log');
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Response>(
      future: _activityFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator(color: AppColors.accent));
        if (snapshot.hasError) {
          return Center(child: Text('ERROR LOADING LOGS', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)));
        }
        final activities = snapshot.data?.data as List? ?? [];
        if (activities.isEmpty) return Center(child: Text('NO ACTIVITY RECORDED', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)));

        return ListView.builder(
          padding: const EdgeInsets.all(24),
          itemCount: activities.length,
          itemBuilder: (context, index) {
            final activity = activities[index];
            final timestamp = activity['timestamp'] != null ? DateTime.parse(activity['timestamp']) : null;
            IconData icon = Icons.info_outline;
            Color color = Colors.white24;
            
            switch (activity['type']) {
              case 'service': icon = Icons.room_service_outlined; color = AppColors.accent; break;
              case 'booking': icon = Icons.event_available; color = Colors.blueAccent; break;
              case 'maintenance': icon = Icons.build_outlined; color = Colors.redAccent; break;
            }

            return Container(
              margin: const EdgeInsets.only(bottom: 16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(color: color.withOpacity(0.1), shape: BoxShape.circle),
                    child: Icon(icon, color: color, size: 16),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(activity['description'] ?? "No description", style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Text(activity['performed_by']?.toUpperCase() ?? "SYSTEM", style: TextStyle(color: color.withOpacity(0.6), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                            const Spacer(),
                            Text(timestamp != null ? DateFormat('MMM d, hh:mm a').format(timestamp) : "", style: const TextStyle(color: Colors.white24, fontSize: 9)),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}

class _SliverAppBarDelegate extends SliverPersistentHeaderDelegate {
  _SliverAppBarDelegate(this._widget);

  final Widget _widget;

  @override
  double get minExtent => 70; // Height of the TabBar container
  @override
  double get maxExtent => 70;

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return _widget;
  }

  @override
  bool shouldRebuild(_SliverAppBarDelegate oldDelegate) {
    return false;
  }
}

class _RoomPhysicalItemsTab extends StatefulWidget {
  final int? inventoryLocationId;
  const _RoomPhysicalItemsTab({this.inventoryLocationId});

  @override
  State<_RoomPhysicalItemsTab> createState() => _RoomPhysicalItemsTabState();
}

class _RoomPhysicalItemsTabState extends State<_RoomPhysicalItemsTab> with SingleTickerProviderStateMixin {
  late Future<Response> _itemsFuture;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _refresh();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _refresh() {
    if (widget.inventoryLocationId != null) {
      _itemsFuture = context.read<ApiService>().dio.get('/inventory/locations/${widget.inventoryLocationId}/items');
    } else {
      _itemsFuture = Future.error("NO LOCATION SYNCED");
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.inventoryLocationId == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inventory_2_outlined, color: Colors.white10, size: 48),
            const SizedBox(height: 16),
            Text('NO INVENTORY LOCATION SYNCED', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)),
            const SizedBox(height: 8),
            Text('Items are tracked via inventory module', style: TextStyle(color: Colors.white24, fontSize: 9)),
          ],
        ),
      );
    }

    return FutureBuilder<Response>(
      future: _itemsFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator(color: AppColors.accent));
        if (snapshot.hasError) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, color: Colors.redAccent, size: 24),
                const SizedBox(height: 16),
                Text('ERROR LOADING ITEMS', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w900, fontSize: 11, letterSpacing: 1)),
                const SizedBox(height: 16),
                TextButton(
                  onPressed: () => setState(() => _refresh()),
                  child: Text("RETRY", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900, fontSize: 12)),
                ),
              ],
            ),
          );
        }
        
        final items = snapshot.data?.data['items'] as List? ?? [];
        
        final fixedItems = items.where((it) => (it['type'] == 'asset' || it['is_fixed_asset'] == true) && it['is_rentable'] != true).toList();
        final rentItems = items.where((it) => it['is_rentable'] == true).toList();
        final consumables = items.where((it) => it['type'] == 'consumable' && it['is_rentable'] != true).toList();
        
        return Column(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              child: TabBar(
                controller: _tabController,
                isScrollable: true,
                indicatorColor: AppColors.accent,
                indicatorWeight: 1,
                labelColor: AppColors.accent,
                unselectedLabelColor: Colors.white24,
                labelStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1),
                dividerColor: Colors.transparent,
                tabs: [
                  Tab(text: "FIXED (${fixedItems.length})"),
                  Tab(text: "RENTED (${rentItems.length})"),
                  Tab(text: "STOCK (${consumables.length})"),
                ],
              ),
            ),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildItemsList(fixedItems, "NO FIXED ASSETS"),
                  _buildItemsList(rentItems, "NO RENTED ITEMS"),
                  _buildItemsList(consumables, "NO STOCK ITEMS"),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildItemsList(List items, String emptyMsg) {
    if (items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.inventory_2_outlined, color: Colors.white10, size: 32),
            const SizedBox(height: 16),
            Text(emptyMsg, style: TextStyle(color: Colors.white38, fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1)),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
      physics: const BouncingScrollPhysics(),
      itemCount: items.length,
      itemBuilder: (context, index) {
            final item = items[index];
            final isAsset = item['type'] == 'asset';
            final isRented = item['is_rentable'] == true;
            final isDamaged = item['is_damaged'] == true;
            
            Color itemColor = Colors.white;
            if (isDamaged) itemColor = Colors.redAccent;
            else if (isRented) itemColor = Colors.blueAccent;

            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: OnyxGlassCard(
                padding: const EdgeInsets.all(16),
                borderColor: itemColor.withOpacity(0.05),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(color: itemColor.withOpacity(0.05), shape: BoxShape.circle),
                      child: Icon(
                        isAsset ? Icons.chair_outlined : Icons.inventory_2_outlined, 
                        color: itemColor.withOpacity(0.8), 
                        size: 18
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  item['item_name']?.toString().toUpperCase() ?? "UNKNOWN ITEM", 
                                  style: TextStyle(color: itemColor, fontWeight: FontWeight.w900, fontSize: 12, letterSpacing: 0.5)
                                ),
                              ),
                              if (isDamaged)
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(color: Colors.redAccent.withOpacity(0.1), borderRadius: BorderRadius.circular(8)),
                                  child: const Text("DAMAGED", style: TextStyle(color: Colors.redAccent, fontSize: 8, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                                ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Text(
                                "${item['current_stock']} ${item['unit'] ?? 'PCS'}".toUpperCase(), 
                                style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 0.5)
                              ),
                              const SizedBox(width: 8),
                              if (isRented) ...[
                                Container(width: 3, height: 3, decoration: BoxDecoration(color: Colors.white10, shape: BoxShape.circle)),
                                const SizedBox(width: 8),
                                Text("RENTAL", style: TextStyle(color: Colors.blueAccent.withOpacity(0.6), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
                              ],
                              const SizedBox(width: 8),
                              Container(width: 3, height: 3, decoration: BoxDecoration(color: Colors.white10, shape: BoxShape.circle)),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  item['category_name']?.toString().toUpperCase() ?? "GENERAL", 
                                  style: TextStyle(color: Colors.white.withOpacity(0.2), fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
  }

}

class _PackageManagerTab extends StatelessWidget {
  const _PackageManagerTab();

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<PackageProvider>();
    
    return RefreshIndicator(
      backgroundColor: AppColors.onyx,
      color: AppColors.accent,
      onRefresh: () => provider.fetchPackages(),
      child: CustomScrollView(
        physics: const BouncingScrollPhysics(),
        slivers: [
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
            sliver: SliverToBoxAdapter(
              child: Row(
                children: [
                  const Text("ACTIVE PACKAGES", style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Colors.white54, letterSpacing: 1)),
                  const Spacer(),
                  Text("${provider.packages.length} OFFERS", style: TextStyle(fontSize: 9, color: Colors.white24, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ),
          if (provider.packages.isEmpty && !provider.isLoading)
            SliverFillRemaining(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.loyalty_outlined, size: 48, color: Colors.white.withOpacity(0.05)),
                    const SizedBox(height: 16),
                    Text("NO PACKAGES CREATED", style: TextStyle(color: Colors.white.withOpacity(0.2), fontWeight: FontWeight.w900, fontSize: 10, letterSpacing: 1.5)),
                  ],
                ),
              ),
            )
          else
            SliverList(
              delegate: SliverChildBuilderDelegate(
                (context, index) {
                  final pkg = provider.packages[index];
                  return Padding(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
                    child: _PackageCard(package: pkg),
                  );
                },
                childCount: provider.packages.length,
              ),
            ),
          const SliverToBoxAdapter(child: SizedBox(height: 100)),
        ],
      ),
    );
  }
}

class _PackageCard extends StatelessWidget {
  final PackageModel package;
  const _PackageCard({required this.package});

  @override
  Widget build(BuildContext context) {
    return OnyxGlassCard(
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Stack(
            children: [
              if (package.images.isNotEmpty)
                _buildHeroImage(ApiConstants.imageBaseUrl + package.images.first)
              else
                Container(
                  height: 140,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
                  ),
                  child: const Center(child: Icon(Icons.image_outlined, color: Colors.white10, size: 32)),
                ),
              Positioned(
                top: 12, right: 12,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(color: Colors.amberAccent, borderRadius: BorderRadius.circular(10)),
                  child: Text(
                    "₹${package.price.toInt()}",
                    style: const TextStyle(color: AppColors.onyx, fontWeight: FontWeight.w900, fontSize: 12),
                  ),
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(package.title.toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 0.5)),
                const SizedBox(height: 4),
                Text(package.description, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 11, height: 1.4)),
                const SizedBox(height: 12),
                Row(
                  children: [
                    _buildTinyTag(Icons.people_outline, "${package.defaultAdults} ADULTS"),
                    const SizedBox(width: 8),
                    if (package.maxStayDays != null)
                      _buildTinyTag(Icons.calendar_today_outlined, "${package.maxStayDays} DAYS MAX"),
                  ],
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () {
                           // Edit Logic
                           final screenState = context.findAncestorStateOfType<_ManagerRoomMgmtScreenState>();
                           screenState?._showPackageForm(package: package);
                        },
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(color: Colors.white.withOpacity(0.1)),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                        child: const Text("EDIT", style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w900)),
                      ),
                    ),
                    const SizedBox(width: 12),
                    IconButton(
                      onPressed: () => _confirmDelete(context, package),
                      icon: const Icon(Icons.delete_outline, color: Colors.redAccent, size: 18),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.redAccent.withOpacity(0.1),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeroImage(String url) {
    return Container(
      height: 140,
      decoration: BoxDecoration(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        image: DecorationImage(image: NetworkImage(url), fit: BoxFit.cover),
      ),
    );
  }

  Widget _buildTinyTag(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(8)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 10, color: Colors.white38),
          const SizedBox(width: 4),
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  void _confirmDelete(BuildContext context, PackageModel pkg) {
    showDialog(
      context: context,
      builder: (ctx) => OnyxGlassDialog(
        title: "DELETE PACKAGE",
        children: [
          Text("ARE YOU SURE YOU WANT TO DELETE \"${pkg.title.toUpperCase()}\"?", textAlign: TextAlign.center, style: TextStyle(color: Colors.white70, fontSize: 12)),
        ],
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("CANCEL")),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(ctx);
              final success = await context.read<PackageProvider>().deletePackage(pkg.id);
              if (success) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("PACKAGE DELETED")));
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
            child: const Text("DELETE"),
          ),
        ],
      ),
    );
  }
}

class _PackageFormDialog extends StatefulWidget {
  final PackageModel? package;
  const _PackageFormDialog({this.package});

  @override
  State<_PackageFormDialog> createState() => _PackageFormDialogState();
}

class _PackageFormDialogState extends State<_PackageFormDialog> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _descController;
  late TextEditingController _priceController;
  late TextEditingController _adultsController;
  late TextEditingController _childrenController;
  late TextEditingController _stayController;
  late TextEditingController _complimentaryController;
  late TextEditingController _themeController;
  
  String _bookingType = "room_type";
  bool _breakfast = false;
  bool _lunch = false;
  bool _dinner = false;
  
  List<XFile> _newImages = [];
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.package?.title);
    _descController = TextEditingController(text: widget.package?.description);
    _priceController = TextEditingController(text: widget.package?.price.toString());
    _adultsController = TextEditingController(text: (widget.package?.defaultAdults ?? 2).toString());
    _childrenController = TextEditingController(text: (widget.package?.defaultChildren ?? 0).toString());
    _stayController = TextEditingController(text: widget.package?.maxStayDays?.toString() ?? "");
    _complimentaryController = TextEditingController(text: widget.package?.complimentary);
    _themeController = TextEditingController(text: widget.package?.theme);
    
    _bookingType = widget.package?.bookingType ?? "room_type";
    final food = widget.package?.foodIncluded?.toLowerCase() ?? "";
    _breakfast = food.contains("breakfast");
    _lunch = food.contains("lunch");
    _dinner = food.contains("dinner");
  }

  Future<void> _pickImages() async {
    final picker = ImagePicker();
    final images = await picker.pickMultiImage();
    if (images.isNotEmpty) {
      setState(() => _newImages.addAll(images));
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    
    setState(() => _isSaving = true);
    
    final foodItems = [
      if (_breakfast) "Breakfast",
      if (_lunch) "Lunch",
      if (_dinner) "Dinner",
    ];

    final formData = FormData.fromMap({
      'title': _titleController.text,
      'description': _descController.text,
      'price': double.parse(_priceController.text),
      'booking_type': _bookingType,
      'default_adults': int.parse(_adultsController.text),
      'default_children': int.parse(_childrenController.text),
      if (_stayController.text.isNotEmpty) 'max_stay_days': int.parse(_stayController.text),
      'food_included': foodItems.join(", "),
      'complimentary': _complimentaryController.text,
      'theme': _themeController.text,
      'status': 'active',
    });

    for (var i = 0; i < _newImages.length; i++) {
      formData.files.add(MapEntry(
        'images',
        await MultipartFile.fromFile(_newImages[i].path, filename: 'pkg_img_$i.jpg'),
      ));
    }

    final provider = context.read<PackageProvider>();
    bool success;
    if (widget.package == null) {
      success = await provider.createPackage(formData);
    } else {
      success = await provider.updatePackage(widget.package!.id, formData);
    }

    setState(() => _isSaving = false);
    if (success) {
      Navigator.pop(context);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(widget.package == null ? "PACKAGE CREATED" : "PACKAGE UPDATED")));
    } else {
       ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("OPERATION FAILED"), backgroundColor: Colors.redAccent));
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.9,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      builder: (context, scrollController) => Container(
        decoration: BoxDecoration(
          color: AppColors.onyx,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
        ),
        child: ClipRRect(
          borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
            child: Column(
              children: [
                Container(
                  width: 40, height: 4,
                  margin: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2)),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                  child: Row(
                    children: [
                      Text(widget.package == null ? "CREATE PACKAGE" : "EDIT PACKAGE", style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: 1)),
                      const Spacer(),
                      if (_isSaving)
                        const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.accent))
                      else
                        TextButton(
                          onPressed: _save,
                          child: const Text("SAVE", style: TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900)),
                        ),
                    ],
                  ),
                ),
                const Divider(color: Colors.white10),
                Expanded(
                  child: Form(
                    key: _formKey,
                    child: ListView(
                      controller: scrollController,
                      padding: const EdgeInsets.all(24),
                      children: [
                        _buildField("PACKAGE NAME", _titleController, Icons.loyalty_outlined),
                        _buildField("DESCRIPTION", _descController, Icons.description_outlined, maxLines: 3),
                        _buildField("THEME", _themeController, Icons.palette_outlined),
                        _buildField("BASE PRICE (₹)", _priceController, Icons.payments_outlined, keyboardType: TextInputType.number),
                        
                        const SizedBox(height: 16),
                        const Text("BOOKING SCOPE", style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
                        const SizedBox(height: 8),
                        _buildScopeSelector(),

                        const SizedBox(height: 24),
                        Row(
                          children: [
                            Expanded(child: _buildField("ADULTS", _adultsController, Icons.person_outline, keyboardType: TextInputType.number)),
                            const SizedBox(width: 16),
                            Expanded(child: _buildField("CHILDREN", _childrenController, Icons.child_care_outlined, keyboardType: TextInputType.number)),
                          ],
                        ),
                        
                        _buildField("MAX STAY (DAYS)", _stayController, Icons.calendar_today_outlined, keyboardType: TextInputType.number),
                        _buildField("INCLUSIONS / COMPLIMENTARY", _complimentaryController, Icons.star_outline, maxLines: 2),

                        const SizedBox(height: 16),
                        const Text("FOOD INCLUDED", style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 12,
                          children: [
                            _buildFoodChip("BREAKFAST", _breakfast, (v) => setState(() => _breakfast = v)),
                            _buildFoodChip("LUNCH", _lunch, (v) => setState(() => _lunch = v)),
                            _buildFoodChip("DINNER", _dinner, (v) => setState(() => _dinner = v)),
                          ],
                        ),

                        const SizedBox(height: 32),
                        const Text("GALLERY IMAGES", style: TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
                        const SizedBox(height: 12),
                        _buildImagePicker(),
                        
                        const SizedBox(height: 100),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildField(String label, TextEditingController controller, IconData icon, {int maxLines = 1, TextInputType? keyboardType}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
          const SizedBox(height: 8),
          TextFormField(
            controller: controller,
            maxLines: maxLines,
            keyboardType: keyboardType,
            style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: Colors.white24, size: 18),
              filled: true,
              fillColor: Colors.white.withOpacity(0.05),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
              enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: const BorderSide(color: AppColors.accent, width: 1)),
              contentPadding: const EdgeInsets.all(16),
            ),
            validator: (v) => v == null || v.isEmpty ? "REQUIRED" : null,
          ),
        ],
      ),
    );
  }

  Widget _buildScopeSelector() {
    return Row(
      children: [
        _buildChoiceChip("ROOM TYPES", _bookingType == "room_type", () => setState(() => _bookingType = "room_type")),
        const SizedBox(width: 12),
        _buildChoiceChip("ENTIRE RESORT", _bookingType == "resort", () => setState(() => _bookingType = "resort")),
      ],
    );
  }

  Widget _buildChoiceChip(String label, bool isSelected, VoidCallback onTap) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: isSelected ? AppColors.accent.withOpacity(0.1) : Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: isSelected ? AppColors.accent.withOpacity(0.3) : Colors.transparent),
          ),
          child: Center(
            child: Text(label, style: TextStyle(color: isSelected ? AppColors.accent : Colors.white38, fontSize: 10, fontWeight: FontWeight.w900)),
          ),
        ),
      ),
    );
  }

  Widget _buildFoodChip(String label, bool isSelected, Function(bool) onChanged) {
    return FilterChip(
      label: Text(label, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w900, color: isSelected ? AppColors.onyx : Colors.white38)),
      selected: isSelected,
      onSelected: onChanged,
      selectedColor: Colors.amberAccent,
      backgroundColor: Colors.white.withOpacity(0.05),
      checkmarkColor: AppColors.onyx,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    );
  }

  Widget _buildImagePicker() {
    return Container(
      height: 100,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          GestureDetector(
            onTap: _pickImages,
            child: Container(
              width: 100,
              decoration: BoxDecoration(color: Colors.white.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white10, style: BorderStyle.solid)),
              child: const Icon(Icons.add_photo_alternate_outlined, color: Colors.white24),
            ),
          ),
          ..._newImages.map((file) => Container(
            width: 100,
            margin: const EdgeInsets.only(left: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: kIsWeb 
                ? Image.network(file.path, fit: BoxFit.cover)
                : Image.file(File(file.path), fit: BoxFit.cover),
            ),
          )),
        ],
      ),
    );
  }
}


