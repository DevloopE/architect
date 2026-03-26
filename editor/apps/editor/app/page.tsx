'use client'

import { BridgeProvider, ConstructionPanel, Dashboard, Editor } from '@pascal-app/editor'

export default function Home() {
  return (
    <div className="h-screen w-screen" style={{ paddingTop: 40 }}>
      <BridgeProvider />
      <Dashboard />
      <Editor projectId="local-editor" />
      <ConstructionPanel />
    </div>
  )
}
