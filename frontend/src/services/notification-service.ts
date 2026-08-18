import { get, post } from "./api-client";
export interface Notification { id: number; notification_type: string; title: string; message: string; study_plan_id: number | null; created_at: string; read_at: string | null; }
export const listNotifications = () => get<Notification[]>("/api/notifications/", { authenticated: true });
export const unreadCount = () => get<{ unread_count: number }>("/api/notifications/unread-count/", { authenticated: true });
export const markNotificationRead = (id: number) => post<Notification>(`/api/notifications/${id}/read/`, undefined, { authenticated: true });
