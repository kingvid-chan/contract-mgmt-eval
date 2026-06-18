import { BrowserRouter, Routes, Route } from 'react-router-dom'

function Home() {
  return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <h1>合同管理系统</h1>
      <p>Contract Management System v0.0.1</p>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter basename="/projects/contract-mgmt-eval">
      <Routes>
        <Route path="/" element={<Home />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
