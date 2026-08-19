import type { ReactNode } from 'react'
export type Status = 'Active' | 'Inactive' | 'Pending'
export type Vendor = { id:string; name:string; category:string; owner:string; initials:string; phone:string; email:string; orders:number; address:string; status:Status }
export type Column<T> = { key:string; label:string; render:(row:T)=>ReactNode; className?:string }
