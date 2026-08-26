import { type ReactNode, useEffect, useState } from 'react'
import { Bike, CalendarDays, CircleDollarSign, Clock3, MapPin, Package, Phone, Store, UserRound, X } from 'lucide-react'
import { getOrder } from './api'
import { Badge, IconButton } from './components'
import type { Order } from './types'

const dateTime=(value:string)=>new Intl.DateTimeFormat(undefined,{dateStyle:'medium',timeStyle:'short'}).format(new Date(value))

export function OrderDetails({orderId,onClose}:{orderId:string|null;onClose:()=>void}){
 const [order,setOrder]=useState<Order|null>(null);const [error,setError]=useState('')
 useEffect(()=>{if(!orderId)return;const controller=new AbortController();setOrder(null);setError('');getOrder(orderId,controller.signal).then(setOrder).catch(err=>{if(err.name!=='AbortError')setError('Unable to load order details. Please try again.')});return()=>controller.abort()},[orderId])
 useEffect(()=>{if(!orderId)return;const close=(event:KeyboardEvent)=>{if(event.key==='Escape')onClose()};document.addEventListener('keydown',close);return()=>document.removeEventListener('keydown',close)},[orderId,onClose])
 if(!orderId)return null
 return <div className="details-backdrop" role="presentation" onMouseDown={onClose}><aside className="details-panel" role="dialog" aria-modal="true" aria-labelledby="order-details-title" onMouseDown={event=>event.stopPropagation()}><header><div><p className="eyebrow">Shipment record</p><h2 id="order-details-title">Order details</h2></div><IconButton label="Close order details" onClick={onClose}><X size={18}/></IconButton></header>{error?<div className="api-error">{error}</div>:!order?<div className="details-loading">Loading order details…</div>:<div className="details-content"><div className="order-hero"><span className="order-icon"><Package/></span><div><h3>{order.reference}</h3><p>{order.vendorName}</p></div><Badge status={order.status}/></div><section className="details-section"><h4>Delivery</h4><Detail icon={<MapPin/>} label="Pickup location" value={order.pickupAddress}/><Detail icon={<MapPin/>} label="Delivery destination" value={order.deliveryAddress}/><Detail icon={<CircleDollarSign/>} label="Delivery fee" value={formatMoney(order.deliveryFee)}/></section><section className="details-section"><h4>People</h4><Detail icon={<Store/>} label="Vendor" value={order.vendorName}/><Detail icon={<UserRound/>} label="Recipient" value={order.recipientName}/><Detail icon={<Phone/>} label="Recipient phone" value={order.recipientPhone}/><Detail icon={<Bike/>} label="Assigned rider" value={order.riderName||'Not assigned'}/></section><section className="details-section"><h4>Record</h4><Detail icon={<Package/>} label="Order ID" value={order.id}/><Detail icon={<CalendarDays/>} label="Created" value={dateTime(order.createdAt)}/><Detail icon={<Clock3/>} label="Last updated" value={dateTime(order.updatedAt)}/></section></div>}</aside></div>
}
function formatMoney(value:string){const amount=Number(value);return Number.isFinite(amount)?new Intl.NumberFormat('en-NG',{style:'currency',currency:'NGN'}).format(amount):value}
function Detail({icon,label,value}:{icon:ReactNode;label:string;value:string}){return <div className="detail-row"><span className="detail-icon">{icon}</span><div><span>{label}</span><strong>{value}</strong></div></div>}
