import { type ReactNode, useEffect, useState } from 'react'
import { Building2, CalendarDays, Mail, MapPin, Phone, ShoppingBag, X } from 'lucide-react'
import { getVendor } from './api'
import { Avatar, Badge, IconButton } from './components'
import type { Vendor } from './types'

type Props = { vendorId:string|null; onClose:()=>void }

export function VendorDetails({vendorId,onClose}:Props){
 const [vendor,setVendor]=useState<Vendor|null>(null);const [error,setError]=useState('');
 useEffect(()=>{if(!vendorId)return;const controller=new AbortController();setVendor(null);setError('');getVendor(vendorId,controller.signal).then(setVendor).catch(err=>{if(err.name!=='AbortError')setError('Unable to load vendor details. Please try again.')});return()=>controller.abort()},[vendorId]);
 useEffect(()=>{const close=(event:KeyboardEvent)=>{if(event.key==='Escape')onClose()};document.addEventListener('keydown',close);return()=>document.removeEventListener('keydown',close)},[onClose]);
 if(!vendorId)return null;
 return <div className="details-backdrop" role="presentation" onMouseDown={onClose}><aside className="details-panel" role="dialog" aria-modal="true" aria-labelledby="vendor-details-title" onMouseDown={event=>event.stopPropagation()}><header><div><p className="eyebrow">Vendor profile</p><h2 id="vendor-details-title">Vendor details</h2></div><IconButton label="Close vendor details" onClick={onClose}><X size={18}/></IconButton></header>{error?<div className="api-error">{error}</div>:!vendor?<div className="details-loading">Loading vendor details…</div>:<div className="details-content"><div className="vendor-hero"><Avatar initials={vendor.initials}/><div><h3>{vendor.name}</h3><p>{vendor.category}</p></div><Badge status={vendor.status}/></div><section className="details-section"><h4>Business information</h4><Detail icon={<Building2/>} label="Business type" value={vendor.category}/><Detail icon={<ShoppingBag/>} label="Orders" value={String(vendor.orders)}/><Detail icon={<MapPin/>} label="Address" value={vendor.address}/></section><section className="details-section"><h4>Owner contact</h4><Detail icon={<span className="detail-initials">{vendor.initials}</span>} label="Owner" value={vendor.owner}/><Detail icon={<Mail/>} label="Email" value={vendor.email}/><Detail icon={<Phone/>} label="Phone" value={vendor.phone}/></section><section className="details-section"><h4>Account</h4><Detail icon={<CalendarDays/>} label="Vendor ID" value={vendor.id}/></section></div>}</aside></div>
}
function Detail({icon,label,value}:{icon:ReactNode;label:string;value:string}){return <div className="detail-row"><span className="detail-icon">{icon}</span><div><span>{label}</span><strong>{value}</strong></div></div>}
