import { render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { ProjectOptimisation } from './ProjectOptimisation'

const project={id:12,organisation_id:4,name:'Sample warehouse',industry_id:'logistics'}
afterEach(()=>{vi.unstubAllGlobals()})

it('does not let viewers execute company optimisation or claim outcomes before a run',async()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({total:0,items:[]})}))
 render(<ProjectOptimisation project={project} token="temporary-test-token" canRun={false} datasetHash="abc" />)
 expect(screen.getByRole('button',{name:/run verified optimisation/i})).toBeDisabled()
 expect(screen.getByText(/viewer role permits reading saved runs/i)).toBeInTheDocument()
 expect(await screen.findByText(/no runs yet/i)).toBeInTheDocument()
})

it('requires a project CSV before enabling optimisation',()=>{
 vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,json:async()=>({total:0,items:[]})}))
 render(<ProjectOptimisation project={project} token="temporary-test-token" canRun={true} datasetHash={null} />)
 expect(screen.getByRole('button',{name:/run verified optimisation/i})).toBeDisabled()
 expect(screen.getByText(/upload a validated logistics csv/i)).toBeInTheDocument()
})
