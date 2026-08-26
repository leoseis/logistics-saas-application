import type { Order, OrderStatus, Status, Vendor } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'
export type ApiStatus = 'active' | 'inactive' | 'pending'
export type VendorCreateInput = { name:string; business_type:string; owner_name:string; phone:string; email:string; address:string; status:ApiStatus }
export type ApiVendor = { id:string; name:string; business_type:string; owner_name:string; phone:string; email:string; address:string; status:ApiStatus; order_count:number; created_at?:string; updated_at?:string }
type Page<T> = { count:number; next:string|null; previous:string|null; results:T[] }
export type ApiOrderStatus = 'pending' | 'assigned' | 'picked_up' | 'delivered' | 'cancelled'
export type ApiOrder = { id:string; reference:string; vendor:string; vendor_name:string; rider:string|null; rider_name:string|null; pickup_address:string; delivery_address:string; recipient_name:string; recipient_phone:string; status:ApiOrderStatus; delivery_fee:string; created_at:string; updated_at:string }
export type VendorDashboard = { total_vendors:number; active_vendors:number; inactive_vendors:number; pending_vendors:number; pending:ApiVendor[] }

const statusLabel: Record<ApiStatus, Status> = { active:'Active', inactive:'Inactive', pending:'Pending' }
const initials = (name:string) => name.split(/\s+/).filter(Boolean).slice(0,2).map(word=>word[0]).join('').toUpperCase()
export const toVendor = (vendor:ApiVendor): Vendor => ({ id:vendor.id, name:vendor.name, category:vendor.business_type, owner:vendor.owner_name, initials:initials(vendor.owner_name), phone:vendor.phone, email:vendor.email, orders:vendor.order_count, address:vendor.address, status:statusLabel[vendor.status] })
const orderStatusLabel:Record<ApiOrderStatus,OrderStatus>={pending:'Pending',assigned:'Assigned',picked_up:'Picked up',delivered:'Delivered',cancelled:'Cancelled'}
export const toOrder=(order:ApiOrder):Order=>({id:order.id,reference:order.reference,vendorId:order.vendor,vendorName:order.vendor_name,riderId:order.rider,riderName:order.rider_name,pickupAddress:order.pickup_address,deliveryAddress:order.delivery_address,recipientName:order.recipient_name,recipientPhone:order.recipient_phone,status:orderStatusLabel[order.status],deliveryFee:order.delivery_fee,createdAt:order.created_at,updatedAt:order.updated_at})

async function request<T>(path:string, signal?:AbortSignal, init?:RequestInit):Promise<T>{
 const response = await fetch(`${API_BASE}${path}`, { ...init, headers:{Accept:'application/json', ...init?.headers}, signal })
 if (!response.ok) throw new Error(`API request failed (${response.status})`)
 return response.json() as Promise<T>
}
export function getVendors({page, query, status, signal}:{page:number;query:string;status:string;signal?:AbortSignal}){
 const params = new URLSearchParams({page:String(page),page_size:'6'})
 if(query) params.set('q',query)
 if(status !== 'All') params.set('status',status.toLowerCase())
 return request<Page<ApiVendor>>(`/vendors/?${params}`,signal).then(pageData=>({count:pageData.count,results:pageData.results.map(toVendor)}))
}
export function getVendorDashboard(signal?:AbortSignal){ return request<VendorDashboard>('/dashboard/vendors/',signal) }
export function getVendor(id:string, signal?:AbortSignal){ return request<ApiVendor>(`/vendors/${id}/`,signal).then(toVendor) }
export function updateVendorStatus(id:string, status:ApiStatus){
 return request<ApiVendor>(`/vendors/${id}/`, undefined, { method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({status}) }).then(toVendor)
}
export function createVendor(payload:VendorCreateInput){
 return request<ApiVendor>('/vendors/', undefined, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }).then(toVendor)
}
export function updateVendor(id:string, payload:VendorCreateInput){
 return request<ApiVendor>(`/vendors/${id}/`, undefined, { method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload) }).then(toVendor)
}
export async function deleteVendor(id:string){
 const response = await fetch(`${API_BASE}/vendors/${id}/`, { method:'DELETE', headers:{Accept:'application/json'} })
 if(!response.ok) throw new Error(`API request failed (${response.status})`)
}
export function getOrders({page,query,status,signal}:{page:number;query:string;status:ApiOrderStatus|'all';signal?:AbortSignal}){
 const params=new URLSearchParams({page:String(page),page_size:'6'})
 if(query)params.set('q',query)
 if(status!=='all')params.set('status',status)
 return request<Page<ApiOrder>>(`/orders/?${params}`,signal).then(data=>({count:data.count,results:data.results.map(toOrder)}))
}
export function getOrder(id:string,signal?:AbortSignal){return request<ApiOrder>(`/orders/${id}/`,signal).then(toOrder)}
