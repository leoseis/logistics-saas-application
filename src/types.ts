import type { ReactNode } from 'react'
import type { ApiOrderStatus } from './api'
export type Status = 'Active' | 'Inactive' | 'Pending' | 'Assigned' | 'Picked up' | 'Delivered' | 'Cancelled' | 'Available' | 'On delivery' | 'Offline'
export type Vendor = { id:string; name:string; category:string; owner:string; initials:string; phone:string; email:string; orders:number; address:string; status:Status }
export type OrderStatus = 'Pending' | 'Assigned' | 'Picked up' | 'Delivered' | 'Cancelled'
export type Order = { id:string; reference:string; vendorId:string; vendorName:string; riderId:string|null; riderName:string|null; riderPhone:string|null; riderStatus:RiderStatus|null; pickupAddress:string; deliveryAddress:string; recipientName:string; recipientPhone:string; status:OrderStatus; statusValue:ApiOrderStatus; deliveryFee:string; createdAt:string; updatedAt:string }
export type RiderStatus='Available'|'On delivery'|'Offline'
export type Rider={id:string;name:string;initials:string;phone:string;email:string;status:RiderStatus;rating:string;activeOrders:number;createdAt:string;updatedAt:string}
export type Column<T> = { key:string; label:string; render:(row:T)=>ReactNode; className?:string }
