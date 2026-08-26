import type { ReactNode } from 'react'
export type Status = 'Active' | 'Inactive' | 'Pending' | 'Assigned' | 'Picked up' | 'Delivered' | 'Cancelled'
export type Vendor = { id:string; name:string; category:string; owner:string; initials:string; phone:string; email:string; orders:number; address:string; status:Status }
export type OrderStatus = 'Pending' | 'Assigned' | 'Picked up' | 'Delivered' | 'Cancelled'
export type Order = { id:string; reference:string; vendorId:string; vendorName:string; riderId:string|null; riderName:string|null; pickupAddress:string; deliveryAddress:string; recipientName:string; recipientPhone:string; status:OrderStatus; deliveryFee:string; createdAt:string; updatedAt:string }
export type Column<T> = { key:string; label:string; render:(row:T)=>ReactNode; className?:string }
