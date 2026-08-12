import { fireEvent, render, screen } from '@testing-library/react'
import { App } from './App'

beforeEach(()=>{localStorage.clear(); location.hash=''})
test('filters vendors by status and search',()=>{
 render(<App />)
 fireEvent.click(screen.getByRole('tab',{name:'Active'}))
 expect(screen.getByText('Swift & Style')).toBeInTheDocument()
 expect(screen.queryByText('Harbor Goods')).not.toBeInTheDocument()
 fireEvent.change(screen.getByLabelText('Search…'),{target:{value:'Maple'}})
 expect(screen.getByText('Maple & Main')).toBeInTheDocument()
 expect(screen.queryByText('Swift & Style')).not.toBeInTheDocument()
})
test('persists theme selection',()=>{
 render(<App />)
 fireEvent.click(screen.getByLabelText('Toggle theme'))
 expect(document.documentElement.dataset.theme).toBe('dark')
 expect(localStorage.getItem('truelog-theme')).toBe('dark')
})
