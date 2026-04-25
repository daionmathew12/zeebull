import re
import os

file_path = r"c:\releasing\New Orchid\Mobile\employee\lib\presentation\screens\manager\manager_room_mgmt_screen.dart"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add api_constants import
if "core/constants/api_constants.dart" not in content:
    content = content.replace(
        "import 'package:orchid_employee/data/models/room_model.dart';",
        "import 'package:orchid_employee/data/models/room_model.dart';\nimport 'package:orchid_employee/core/constants/api_constants.dart';"
    )

# 2. Extract the itemBuilder code using exact slicing or robust regex
# We want to replace from "return Container(" down to ");\n                                  },"
start_idx = content.find("                                    return Container(")
end_idx = content.find("                                  },\n                                ),")

if start_idx != -1 and end_idx != -1:
    new_method = """  Widget _buildRoomCard(Room room, Color statusColor) {
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
                      image: NetworkImage(ApiConstants.baseUrl.replaceAll('/api', '') + room.imageUrl!),
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
"""

    replacement = "                                    return _buildRoomCard(room, statusColor);\n"
    
    content = content[:start_idx] + replacement + content[end_idx:]
    
    # Insert new_method before _buildEmptyState
    content = content.replace("  Widget _buildEmptyState() {", new_method + "\n  Widget _buildEmptyState() {")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully replaced itemBuilder and added _buildRoomCard")
else:
    print(f"Could not find exact slice. Start: {start_idx}, End: {end_idx}")
