import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { IndustryPilotStudio } from './IndustryPilotStudio'

const scenario = {
 industry: 'logistics', objective: 'minimize_cost',
 capacities: {handling_units:9, express_slots:2},
 options: [{item_id:'order_101',option_id:'economy',objective_value:12, resources:{handling_units:3,express_slots:0}}],
 input_provenance: 'synthetic demo',
}
function mockResponse(data:unknown){ return {ok:true,json:async()=>data} }

it('shows provenance and returns the documented solver outcome', async () => {
 const user = userEvent.setup()
 vi.stubGlobal('fetch', vi.fn(async (input:string, init?:RequestInit) => {
  if (input.includes('/catalogue')) return mockResponse({data_sources:[]})
  if (init?.method === 'POST') return mockResponse({
   status:'optimal', objective_value:12, message:'Optimal for the specified finite model',
   input_provenance:'synthetic demo', decisions:[{item_id:'order_101',option_id:'economy',contribution:12}],
   constraint_usage:{handling_units:{used:3,limit:9}},
  })
  return mockResponse({scenario})
 }))
 render(<IndustryPilotStudio />)
 await screen.findByText(/model: minimize cost/i)
 await user.click(screen.getByRole('button',{name:/solve this decision model/i}))
 expect(await screen.findByText(/solver outcome: optimal/i)).toBeInTheDocument()
 expect(screen.getByText(/input provenance: synthetic demo/i)).toBeInTheDocument()
 expect(screen.getByText(/no baseline improvement or realised savings claimed/i)).toBeInTheDocument()
 await waitFor(()=>expect(screen.getByText('order_101')).toBeInTheDocument())
})

it('does not display a made-up optimum for infeasible constraints', async () => {
 const user = userEvent.setup()
 vi.stubGlobal('fetch',vi.fn(async(input:string,init?:RequestInit)=>{
  if(input.includes('/catalogue'))return mockResponse({data_sources:[]})
  if(init?.method==='POST')return mockResponse({status:'infeasible',objective_value:null,message:'No certified optimum',input_provenance:'synthetic demo',decisions:[],constraint_usage:{}})
  return mockResponse({scenario})
 }))
 render(<IndustryPilotStudio />)
 await screen.findByText(/model: minimize cost/i)
 await user.click(screen.getByRole('button',{name:/solve this decision model/i}))
 expect(await screen.findByText(/solver outcome: infeasible/i)).toBeInTheDocument()
 expect(screen.getAllByText('No certified optimum').length).toBeGreaterThan(0)
 expect(screen.queryByText(/hypothetical cost units/i)).not.toBeInTheDocument()
})
