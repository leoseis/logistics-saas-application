import { type FormEvent, useEffect, useState } from 'react'
import { ShieldCheck, X } from 'lucide-react'
import { ApiError, verifyPickup } from './api'
import { Button, IconButton } from './components'
import type { Order } from './types'

export function VerifyPickup({order,onClose,onVerified}:{order:Order;onClose:()=>void;onVerified:(order:Order)=>void}){
 const [code,setCode]=useState('');const [error,setError]=useState('');const [submitting,setSubmitting]=useState(false)
 useEffect(()=>{const close=(event:KeyboardEvent)=>{if(event.key==='Escape'&&!submitting)onClose()};document.addEventListener('keydown',close);return()=>document.removeEventListener('keydown',close)},[onClose,submitting])
 const submit=async(event:FormEvent)=>{event.preventDefault();if(!/^\d{6}$/.test(code)){setError('Enter the 6-digit pickup code.');return}setSubmitting(true);setError('');try{onVerified(await verifyPickup(order.id,code))}catch(apiError){if(apiError instanceof ApiError&&apiError.status===400)setError('Invalid pickup code.');else setError('Unable to verify pickup. Please try again.')}finally{setSubmitting(false)}}
 return <div className="details-backdrop verify-backdrop" role="presentation" onMouseDown={()=>!submitting&&onClose()}><section className="verify-dialog" role="dialog" aria-modal="true" aria-labelledby="verify-pickup-title" onMouseDown={event=>event.stopPropagation()}><header><span className="verify-icon"><ShieldCheck/></span><IconButton label="Close pickup verification" onClick={onClose} disabled={submitting}><X size={18}/></IconButton></header><h2 id="verify-pickup-title">Verify Package Pickup</h2><div className="verify-order"><span>Order <strong>{order.reference}</strong></span><span>Rider <strong>{order.riderName||'Not assigned'}</strong></span></div><form onSubmit={submit}><label className="form-field"><span>Pickup code</span><input aria-label="Pickup code" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={code} onChange={event=>{setCode(event.target.value.replace(/\D/g,''));setError('')}} autoFocus/>{error&&<small role="alert">{error}</small>}</label><footer><Button type="button" onClick={onClose} disabled={submitting}>Cancel</Button><Button type="submit" variant="primary" loading={submitting}>Verify Pickup</Button></footer></form></section></div>
}
