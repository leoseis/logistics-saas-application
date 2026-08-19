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
test('persists theme selection',()=>{
 render(<App />)
 fireEvent.click(screen.getByLabelText('Toggle theme'))
 expect(document.documentElement.dataset.theme).toBe('dark')
 expect(localStorage.getItem('truelog-theme')).toBe('dark')
})
