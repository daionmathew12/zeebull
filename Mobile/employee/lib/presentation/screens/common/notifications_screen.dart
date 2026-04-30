
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../../core/constants/app_colors.dart';
import '../../providers/notification_provider.dart';
import '../../../data/models/notification_model.dart';
import '../../widgets/onyx_glass_card.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Provider.of<NotificationProvider>(context, listen: false).fetchNotifications();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.onyx,
      appBar: AppBar(
        title: const Text("NOTIFICATIONS", style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1.5)),
        backgroundColor: AppColors.onyx,
        elevation: 0,
        iconTheme: const IconThemeData(color: AppColors.accent),
        actions: [
          IconButton(
            icon: const Icon(Icons.done_all, color: AppColors.accent),
            tooltip: 'Mark all as read',
            onPressed: () {
              Provider.of<NotificationProvider>(context, listen: false).markAllAsRead();
            },
          ),
          IconButton(
            icon: const Icon(Icons.delete_sweep, color: Colors.redAccent),
            tooltip: 'Clear all',
            onPressed: () {
              Provider.of<NotificationProvider>(context, listen: false).clearAll();
            },
          ),
        ],
      ),
      body: Consumer<NotificationProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.notifications.isEmpty) {
            return const Center(child: CircularProgressIndicator(color: AppColors.accent));
          }

          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text("Error: ${provider.error}", style: const TextStyle(color: Colors.redAccent)),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.fetchNotifications(),
                    style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: AppColors.onyx),
                    child: const Text("RETRY"),
                  )
                ],
              ),
            );
          }

          if (provider.notifications.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.notifications_off_outlined, size: 64, color: Colors.white.withOpacity(0.05)),
                  const SizedBox(height: 16),
                  Text("NO NOTIFICATIONS", style: TextStyle(color: Colors.white.withOpacity(0.1), fontWeight: FontWeight.w900, fontSize: 14, letterSpacing: 1)),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              await provider.fetchNotifications();
            },
            color: AppColors.accent,
            backgroundColor: AppColors.onyx,
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: provider.notifications.length,
              itemBuilder: (context, index) {
                final note = provider.notifications[index];
                return _buildNotificationCard(context, note, provider);
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildNotificationCard(BuildContext context, AppNotification note, NotificationProvider provider) {
    final bool isUnread = !note.isRead;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: OnyxGlassCard(
        padding: EdgeInsets.zero,
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          leading: Stack(
            children: [
              _getIconForType(note.type),
              if (isUnread)
                Positioned(
                  right: 0,
                  top: 0,
                  child: Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      color: AppColors.accent,
                      shape: BoxShape.circle,
                      border: Border.all(color: AppColors.onyx, width: 2),
                    ),
                  ),
                ),
            ],
          ),
          title: Text(
            note.title.toUpperCase(),
            style: TextStyle(
              color: Colors.white,
              fontWeight: isUnread ? FontWeight.w900 : FontWeight.bold,
              fontSize: 14,
              letterSpacing: 0.5,
            ),
          ),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 6),
              Text(
                note.message,
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 13,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                _formatTimestamp(note.createdAt).toUpperCase(),
                style: const TextStyle(
                  color: AppColors.accent,
                  fontSize: 10,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
          onTap: () {
            if (isUnread) {
              provider.markAsRead(note.id);
            }
          },
        ),
      ),
    );
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final diff = now.difference(timestamp);
    if (diff.inMinutes < 60) {
      return "${diff.inMinutes}m ago";
    } else if (diff.inHours < 24) {
      return "${diff.inHours}h ago";
    } else {
      return DateFormat('MMM d, h:mm a').format(timestamp);
    }
  }

  Widget _getIconForType(String type) {
    IconData icon;
    Color color;
    switch (type.toLowerCase()) {
      case 'service':
      case 'assignment':
        icon = Icons.assignment_rounded;
        color = Colors.blueAccent;
        break;
      case 'booking':
        icon = Icons.confirmation_number_rounded;
        color = Colors.greenAccent;
        break;
      case 'finance':
      case 'expense':
        icon = Icons.account_balance_wallet_rounded;
        color = Colors.orangeAccent;
        break;
      case 'food_order':
        icon = Icons.restaurant_rounded;
        color = Colors.redAccent;
        break;
      case 'maintenance':
        icon = Icons.build_rounded;
        color = Colors.purpleAccent;
        break;
      case 'info':
      default:
        icon = Icons.notifications_active_rounded;
        color = AppColors.accent;
    }
    
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Icon(icon, color: color, size: 22),
    );
  }
}
