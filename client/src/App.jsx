import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ChakraProvider, Box } from '@chakra-ui/react'
import { ClerkProvider, SignIn, SignUp, SignedIn, SignedOut, RedirectToSignIn } from '@clerk/clerk-react'
import Navigation from './components/Navigation'
import ChatInterface from './components/ChatInterface'

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

function App() {
  return (
    <ClerkProvider publishableKey={clerkPubKey}>
      <ChakraProvider>
        <Router>
          <Box minH="100vh">
            <Navigation />
            <Routes>
              <Route path="/sign-in/*" element={<SignIn routing="path" path="/sign-in" />} />
              <Route path="/sign-up/*" element={<SignUp routing="path" path="/sign-up" />} />
              
              <Route
                path="/"
                element={
                  <>
                    <SignedIn>
                      <ChatInterface />
                    </SignedIn>
                    <SignedOut>
                      <RedirectToSignIn />
                    </SignedOut>
                  </>
                }
              />
            </Routes>
          </Box>
        </Router>
      </ChakraProvider>
    </ClerkProvider>
  )
}

export default App
