import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { App } from './App'

beforeEach(()=>{localStorage.clear(); location.hash=''})
afterEach(()=>cleanup())
const response = (data:unknown) => Promise.resolve({ok:true,json:async()=>data})
beforeEach(()=>{
 vi.stubGlobal('fetch', vi.fn((input:RequestInfo|URL)=>{
  const url=String(input)
  if(url.includes('dashboard/vendors')) return response({total_vendors:3,active_vendors:1,inactive_vendors:1,pending_vendors:1,pending:[]})
  return response({count:1,next:null,previous:null,results:[{id:'vendor-1',name:'Maple & Main',business_type:'Electric',owner_name:'Ronald Richards',phone:'+234',email:'maple@example.test',address:'Lagos',status:'active',order_count:3}]})
 }))
})
test('loads vendors from the API', async()=>{
 render(<App />)
 expect(await screen.findByText('Maple & Main')).toBeInTheDocument()
 expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/api/vendors/'),expect.any(Object))
})
test('opens vendor details from a row action', async()=>{
 render(<App />)
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
