import { useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { deleteVendor } from './api'
import { Button, IconButton } from './components'
import type { Vendor } from './types'

export function DeleteVendorDialog({vendor,onClose,onDeleted}:{vendor:Vendor;onClose:()=>void;onDeleted:(vendor:Vendor)=>void}){
 const [deleting,setDeleting]=useState(false);const [error,setError]=useState('')
 const remove=async()=>{if(deleting)return;setDeleting(true);setError('');try{await deleteVendor(vendor.id);onDeleted(vendor)}catch{setError(`Unable to delete ${vendor.name}. This vendor may still be linked to delivery orders.`)}finally{setDeleting(false)}}
 return <div className="details-backdrop" role="presentation" onMouseDown={deleting?undefined:onClose}><section className="delete-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-vendor-title" onMouseDown={event=>event.stopPropagation()}><header><span className="delete-icon"><AlertTriangle size={20}/></span><IconButton label="Close delete confirmation" onClick={onClose} disabled={deleting}><X size={18}/></IconButton></header><h2 id="delete-vendor-title">Delete {vendor.name}?</h2><p>This action cannot be undone. The vendor and its profile information will be permanently removed.</p>{error&&<div className="api-error">{error}</div>}<footer><Button onClick={onClose} disabled={deleting}>Cancel</Button><Button className="danger-button" variant="primary" onClick={remove} loading={deleting}>Delete vendor</Button></footer></section></div>
}
