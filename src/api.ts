import type { Order, OrderStatus, Rider, RiderStatus, Status, Vendor } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'
export type ApiStatus = 'active' | 'inactive' | 'pending'
export type VendorCreateInput = { name:string; business_type:string; owner_name:string; phone:string; email:string; address:string; status:ApiStatus }
export type ApiVendor = { id:string; name:string; business_type:string; owner_name:string; phone:string; email:string; address:string; status:ApiStatus; order_count:number; created_at?:string; updated_at?:string }
type Page<T> = { count:number; next:string|null; previous:string|null; results:T[] }
export type ApiOrderStatus = 'pending' | 'assigned' | 'picked_up' | 'delivered' | 'cancelled'
export type ApiOrder = { id:string; reference:string; vendor:string; vendor_name:string; rider:string|null; rider_name:string|null; pickup_address:string; delivery_address:string; recipient_name:string; recipient_phone:string; status:ApiOrderStatus; delivery_fee:string; created_at:string; updated_at:string }
export type OrderCreateInput = { reference:string; vendor:string; rider:string|null; pickup_address:string; delivery_address:string; recipient_name:string; recipient_phone:string; status:ApiOrderStatus; delivery_fee:string }
export type ApiRider = { id:string; full_name:string; phone:string; email:string; status:'available'|'on_delivery'|'offline'; rating:string; active_order_count:number; created_at:string; updated_at:string }
export type ApiRiderStatus=ApiRider['status']
export type RiderInput={full_name:string;phone:string;email:string;status:ApiRiderStatus;rating:string}
export type ApiFieldErrors = Record<string,string[]|string>
export type VendorDashboard = { total_vendors:number; active_vendors:number; inactive_vendors:number; pending_vendors:number; pending:ApiVendor[] }

const statusLabel: Record<ApiStatus, Status> = { active:'Active', inactive:'Inactive', pending:'Pending' }
const initials = (name:string) => name.split(/\s+/).filter(Boolean).slice(0,2).map(word=>word[0]).join('').toUpperCase()
export const toVendor = (vendor:ApiVendor): Vendor => ({ id:vendor.id, name:vendor.name, category:vendor.business_type, owner:vendor.owner_name, initials:initials(vendor.owner_name), phone:vendor.phone, email:vendor.email, orders:vendor.order_count, address:vendor.address, status:statusLabel[vendor.status] })
const orderStatusLabel:Record<ApiOrderStatus,OrderStatus>={pending:'Pending',assigned:'Assigned',picked_up:'Picked up',delivered:'Delivered',cancelled:'Cancelled'}
export const toOrder=(order:ApiOrder):Order=>({id:order.id,reference:order.reference,vendorId:order.vendor,vendorName:order.vendor_name,riderId:order.rider,riderName:order.rider_name,pickupAddress:order.pickup_address,deliveryAddress:order.delivery_address,recipientName:order.recipient_name,recipientPhone:order.recipient_phone,status:orderStatusLabel[order.status],deliveryFee:order.delivery_fee,createdAt:order.created_at,updatedAt:order.updated_at})
const riderStatusLabel:Record<ApiRiderStatus,RiderStatus>={available:'Available',on_delivery:'On delivery',offline:'Offline'}
export const toRider=(rider:ApiRider):Rider=>({id:rider.id,name:rider.full_name,initials:initials(rider.full_name),phone:rider.phone,email:rider.email,status:riderStatusLabel[rider.status],rating:rider.rating,activeOrders:rider.active_order_count,createdAt:rider.created_at,updatedAt:rider.updated_at})

export class ApiError extends Error{constructor(public status:number,public fields:ApiFieldErrors={}){super(`API request failed (${status})`)}}
async function request<T>(path:string, signal?:AbortSignal, init?:RequestInit):Promise<T>{
 const response = await fetch(`${API_BASE}${path}`, { ...init, headers:{Accept:'application/json', ...init?.headers}, signal })
 if (!response.ok){let fields:ApiFieldErrors={};try{fields=await response.json() as ApiFieldErrors}catch{/* Response was not JSON. */}throw new ApiError(response.status,fields)}
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
export function createOrder(payload:OrderCreateInput){return request<ApiOrder>('/orders/',undefined,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(toOrder)}
export function getOrderFormOptions(signal?:AbortSignal){return Promise.all([request<Page<ApiVendor>>('/vendors/?page=1&page_size=100&status=active',signal),request<Page<ApiRider>>('/riders/?page=1&page_size=100',signal)]).then(([vendors,riders])=>({vendors:vendors.results,riders:riders.results}))}
export function getRiders({page,query,status,signal}:{page:number;query:string;status:ApiRiderStatus|'all';signal?:AbortSignal}){const params=new URLSearchParams({page:String(page),page_size:'6'});if(query)params.set('q',query);if(status!=='all')params.set('status',status);return request<Page<ApiRider>>(`/riders/?${params}`,signal).then(data=>({count:data.count,results:data.results.map(toRider)}))}
export function getRider(id:string,signal?:AbortSignal){return request<ApiRider>(`/riders/${id}/`,signal).then(toRider)}
export function createRider(payload:RiderInput){return request<ApiRider>('/riders/',undefined,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(toRider)}
export function updateRider(id:string,payload:RiderInput){return request<ApiRider>(`/riders/${id}/`,undefined,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(toRider)}
export async function deleteRider(id:string){const response=await fetch(`${API_BASE}/riders/${id}/`,{method:'DELETE',headers:{Accept:'application/json'}});if(!response.ok)throw new ApiError(response.status)}
