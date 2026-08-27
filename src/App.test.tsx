import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { App } from './App'

beforeEach(()=>{localStorage.clear(); location.hash=''})
afterEach(()=>cleanup())
const response = (data:unknown) => Promise.resolve({ok:true,json:async()=>data})
const analytics={total_orders:3,pending_orders:1,assigned_orders:0,picked_up_orders:0,delivered_orders:2,cancelled_orders:0,total_revenue:'12000.00',delivered_revenue:'12000.00',pending_revenue:'3000.00',average_order_value:'5000.00',total_weight_kg:'10.00',delivered_weight_kg:'8.00',average_order_weight_kg:'3.33',total_vendors:3,active_vendors:1,pending_vendors:1,inactive_vendors:1,total_riders:2,available_riders:1,riders_on_delivery:1,inactive_riders:0,recent_orders:[],revenue_trend:Array.from({length:7},(_,index)=>({date:`2026-08-${21+index}`,revenue:index===6?'12000.00':'0.00'}))}
beforeEach(()=>{
 vi.stubGlobal('fetch', vi.fn((input:RequestInfo|URL)=>{
  const url=String(input)
  if(url.includes('dashboard/vendors')) return response({total_vendors:3,active_vendors:1,inactive_vendors:1,pending_vendors:1,pending:[]})
  if(url.endsWith('/api/dashboard/')) return response(analytics)
  return response({count:1,next:null,previous:null,results:[{id:'vendor-1',name:'Maple & Main',business_type:'Electric',owner_name:'Ronald Richards',phone:'+234',email:'maple@example.test',address:'Lagos',status:'active',order_count:3}]})
 }))
})
test('loads live dashboard analytics',async()=>{
 render(<App />)
 expect(await screen.findByText('Delivered Revenue')).toBeInTheDocument()
 expect(screen.getAllByText('₦12,000').length).toBeGreaterThan(0)
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/dashboard/'),expect.any(Object))
})
test('loads vendors from the API', async()=>{
 render(<App />)
 fireEvent.click(screen.getByText('Vendors'))
 expect(await screen.findByText('Maple & Main')).toBeInTheDocument()
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/vendors/'),expect.any(Object))
})
test('opens vendor details from a row action', async()=>{
 render(<App />)
 fireEvent.click(screen.getByText('Vendors'))
 await screen.findByText('Maple & Main')
 fireEvent.click(screen.getByLabelText('Vendor actions'))
 fireEvent.click(screen.getByText('View details'))
 expect(await screen.findByRole('dialog', {name:'Vendor details'})).toBeInTheDocument()
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/vendors/vendor-1/'),expect.any(Object))
})
test('persists theme selection',()=>{
 render(<App />)
 fireEvent.click(screen.getByLabelText('Toggle theme'))
 expect(document.documentElement.dataset.theme).toBe('dark')
 expect(localStorage.getItem('truelog-theme')).toBe('dark')
})
test('navigates to orders and opens order details',async()=>{
 const order={id:'order-1',reference:'ORD-1001',vendor:'vendor-1',vendor_name:'Maple & Main',rider:null,rider_name:null,pickup_address:'Lagos Island',delivery_address:'Ikeja',recipient_name:'Ada Okafor',recipient_phone:'+234801',status:'pending',delivery_fee:'2500.00',created_at:'2026-08-20T10:00:00Z',updated_at:'2026-08-20T10:00:00Z'}
 vi.mocked(fetch).mockImplementation((input:RequestInfo|URL)=>String(input).includes('/orders/order-1/')?response(order):String(input).includes('/orders/')?response({count:1,next:null,previous:null,results:[order]}):response({count:0,next:null,previous:null,results:[]}))
 render(<App />)
 fireEvent.click(screen.getByText('Orders'))
 expect(await screen.findByText('ORD-1001')).toBeInTheDocument()
 fireEvent.click(screen.getByLabelText('Actions for order ORD-1001'))
 fireEvent.click(screen.getByText('View details'))
 expect(await screen.findByRole('dialog',{name:'Order details'})).toBeInTheDocument()
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/orders/order-1/'),expect.any(Object))
})
test('shows assigned-order transitions and marks an order as picked up',async()=>{
 const assigned={id:'order-2',reference:'ORD-ASSIGNED',vendor:'vendor-1',vendor_name:'Maple & Main',rider:'rider-1',rider_name:'Tola Driver',rider_phone:'+23480777',rider_status:'on_delivery',pickup_address:'Lagos Island',delivery_address:'Ikeja',recipient_name:'Ada Okafor',recipient_phone:'+234801',status:'assigned',delivery_fee:'2500.00',created_at:'2026-08-20T10:00:00Z',updated_at:'2026-08-20T10:00:00Z'}
 const pickedUp={...assigned,status:'picked_up'}
 let wasPickedUp=false
 vi.mocked(fetch).mockImplementation((input:RequestInfo|URL,init?:RequestInit)=>{const url=String(input);if(url.includes('/orders/order-2/')&&init?.method==='PATCH'){wasPickedUp=true;return response(pickedUp)}if(url.includes('/orders/'))return response({count:1,next:null,previous:null,results:[wasPickedUp?pickedUp:assigned]});return response({count:0,next:null,previous:null,results:[]})})
 render(<App />)
 fireEvent.click(screen.getByText('Orders'))
 await screen.findByText('ORD-ASSIGNED')
 fireEvent.click(screen.getByLabelText('Actions for order ORD-ASSIGNED'))
 expect(screen.getByText('Mark as picked up')).toBeInTheDocument()
 expect(screen.getByText('Cancel order')).toBeInTheDocument()
 fireEvent.click(screen.getByText('Mark as picked up'))
 expect(await screen.findByText('ORD-ASSIGNED was marked as picked up.')).toBeInTheDocument()
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/orders/order-2/'),expect.objectContaining({method:'PATCH',body:JSON.stringify({status:'picked_up'})}))
 expect(screen.getAllByText('Picked up').some(element=>element.classList.contains('badge'))).toBe(true)
})
test('creates an order with the selected vendor UUID',async()=>{
 const created={id:'order-new',reference:'ORD-NEW',vendor:'vendor-1',vendor_name:'Maple & Main',rider:null,rider_name:null,pickup_address:'Marina',delivery_address:'Ikeja',recipient_name:'Ada Okafor',recipient_phone:'+2348012345',status:'pending',weight_kg:'1.00',price_per_kg:'1500.00',delivery_fee:'1500.00',created_at:'2026-08-20T10:00:00Z',updated_at:'2026-08-20T10:00:00Z'}
 vi.mocked(fetch).mockImplementation((input:RequestInfo|URL,init?:RequestInit)=>{const url=String(input);if(url.includes('/vendors/?'))return response({count:1,next:null,previous:null,results:[{id:'vendor-1',name:'Maple & Main',status:'active'}]});if(url.includes('/riders/?'))return response({count:0,next:null,previous:null,results:[]});if(url.includes('/pricing/'))return response({price_per_kg:'1500.00'});if(url.endsWith('/api/orders/')&&init?.method==='POST')return response(created);if(url.includes('/orders/'))return response({count:0,next:null,previous:null,results:[]});return response({count:0,next:null,previous:null,results:[]})})
 render(<App />)
 fireEvent.click(screen.getByText('Orders'))
 fireEvent.click(await screen.findByText('Add Order'))
 await screen.findByRole('option',{name:'Maple & Main'})
 fireEvent.change(screen.getByLabelText('Order reference'),{target:{value:'ORD-NEW'}})
 fireEvent.change(screen.getByLabelText('Vendor'),{target:{value:'vendor-1'}})
 fireEvent.change(screen.getByLabelText('Recipient name'),{target:{value:'Ada Okafor'}})
 fireEvent.change(screen.getByLabelText('Recipient phone'),{target:{value:'+2348012345'}})
 fireEvent.change(screen.getByLabelText('Pickup location'),{target:{value:'Marina'}})
 fireEvent.change(screen.getByLabelText('Delivery destination'),{target:{value:'Ikeja'}})
 fireEvent.change(screen.getByLabelText('Package Weight (kg)'),{target:{value:'1'}})
 fireEvent.click(screen.getByRole('button',{name:'Create order'}))
 expect(await screen.findByText('ORD-NEW was created successfully.')).toBeInTheDocument()
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/orders/'),expect.objectContaining({method:'POST',body:expect.stringContaining('"vendor":"vendor-1"')}))
 const createCall=vi.mocked(fetch).mock.calls.find(([,init])=>init?.method==='POST')
 expect(createCall?.[1]?.body).not.toContain('delivery_fee')
})
test('navigates to riders and opens rider details',async()=>{
 const rider={id:'rider-1',full_name:'Tola Driver',phone:'+23480777',email:'tola@example.com',status:'available',rating:'4.8',active_order_count:2,created_at:'2026-08-20T10:00:00Z',updated_at:'2026-08-20T10:00:00Z'}
 vi.mocked(fetch).mockImplementation((input:RequestInfo|URL)=>String(input).includes('/riders/rider-1/')?response(rider):String(input).includes('/riders/')?response({count:1,next:null,previous:null,results:[rider]}):response({count:0,next:null,previous:null,results:[]}))
 render(<App />)
 fireEvent.click(screen.getByText('Riders'))
 expect(await screen.findByText('Tola Driver')).toBeInTheDocument()
 fireEvent.click(screen.getByLabelText('Actions for rider Tola Driver'))
 fireEvent.click(screen.getByText('View details'))
 expect(await screen.findByRole('dialog',{name:'Rider details'})).toBeInTheDocument()
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/riders/rider-1/'),expect.any(Object))
})
