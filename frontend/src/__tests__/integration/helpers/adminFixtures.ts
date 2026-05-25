export const ADMIN_USERNAME = "sysadmin";
export const ADMIN_PASSWORD = "adminpass123";
export const ADMIN_DISPLAY_NAME = "Quản trị viên hệ thống";

export const adminProfile = {
  id: "665000000000000000000001",
  username: ADMIN_USERNAME,
  display_name: ADMIN_DISPLAY_NAME,
  is_system_admin: true,
  status: "active",
  status_label: "Hoạt động",
  last_login_at_display: "25/05/2025 10:00",
};

export const dashboardStats = {
  new_reports_count: 5,
  pending_students_7d_count: 3,
  new_published_places_7d_count: 12,
  links: {},
};

export const sampleCategories = [
  {
    id: "cat001",
    name: "Quán ăn",
    color: "#EF4444",
    order: 1,
    is_hidden: false,
    place_count: 10,
    created_at_display: "01/01/2025",
  },
  {
    id: "cat002",
    name: "Thư viện",
    color: "#3B82F6",
    order: 2,
    is_hidden: true,
    place_count: 0,
    created_at_display: "15/01/2025",
  },
];
