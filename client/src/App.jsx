import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { ChakraProvider, Box, Flex, VStack, Heading, Text } from '@chakra-ui/react'
import DocumentUpload from './components/DocumentUpload'
import ResultsList from './components/ResultsList'
import ImplementationPlan from './components/ImplementationPlan'
import ComplianceVerification from './components/ComplianceVerification'
import Navigation from './components/Navigation'

function App() {
  return (
    <ChakraProvider>
      <Router>
        <Box minH="100vh" bg="gray.50">
          <Navigation />
          
          <Box maxW="1200px" mx="auto" p={6}>
            <Routes>
              <Route path="/" element={
                <VStack spacing={8} align="stretch">
                  <Heading>RBI Compliance Automation System</Heading>
                  <DocumentUpload />
                  <ResultsList />
                </VStack>
              } />
              
              <Route path="/plan/:id" element={<ImplementationPlan />} />
              <Route path="/verify/:id" element={<ComplianceVerification />} />
              
              <Route path="*" element={
                <Box textAlign="center" py={10}>
                  <Heading size="xl">404: Page Not Found</Heading>
                  <Text mt={4}>The page you're looking for doesn't exist.</Text>
                  <Link to="/">Return Home</Link>
                </Box>
              } />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ChakraProvider>
  )
}

export default App
