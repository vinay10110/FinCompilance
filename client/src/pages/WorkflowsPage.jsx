import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Box, 
  Flex, 
  Alert, 
  AlertIcon, 
  AlertTitle, 
  AlertDescription,
  Spinner,
  useColorModeValue,
  IconButton,
  Tooltip,
  HStack,
  Text
} from '@chakra-ui/react'
import { FiArrowLeft, FiHome } from 'react-icons/fi'
import { useUser } from '@clerk/clerk-react'
import Sidebar from '../components/Sidebar'
import WorkflowChatInterface from '../components/WorkflowChatInterface'
import WorkflowRightSidebar from '../components/WorkflowRightSidebar'

const WorkflowsPage = () => {
  const { workflowId } = useParams()
  const { user } = useUser()
  const navigate = useNavigate()
  const [selectedWorkflow, setSelectedWorkflow] = useState(null)
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(true)
  const [workflowDocuments, setWorkflowDocuments] = useState([])
  
  const bgColor = useColorModeValue('gray.50', 'gray.900')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  // Fetch workflow details if workflowId is provided
  useEffect(() => {
    if (workflowId && user) {
      fetchWorkflow(workflowId)
    }
  }, [workflowId, user])

  const fetchWorkflow = async (id) => {
    try {
      setIsLoading(true)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/workflows/${id}?user_id=${user.id}`)
      const data = await response.json()
      
      if (data.status === 'success') {
        setSelectedWorkflow(data.data.workflow)
      } else {
        console.error('Failed to fetch workflow:', data.message)
      }
    } catch (error) {
      console.error('Error fetching workflow:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDocumentSelect = (update) => {
    setSelectedDoc(update)
  }

  const handleWorkflowDocumentSelect = (document) => {
    setSelectedDoc(document)
  }

  const toggleRightSidebar = () => {
    setIsRightSidebarOpen(!isRightSidebarOpen)
  }

  const handleDocumentsUpdate = () => {
    // This will trigger a re-fetch of documents in WorkflowRightSidebar
    // by updating the key or triggering a refresh
    if (selectedWorkflow) {
      fetchWorkflow(workflowId)
    }
  }

  if (!workflowId) {
    return (
      <Box minH="100vh" bg={bgColor} pt="80px">
        <Flex justify="center" align="center" h="50vh">
          <Alert status="info" maxW="md">
            <AlertIcon />
            <Box>
              <AlertTitle>Select a Workflow</AlertTitle>
              <AlertDescription>
                Please select a workflow from the workflows dialog to start working.
              </AlertDescription>
            </Box>
          </Alert>
        </Flex>
      </Box>
    )
  }

  if (isLoading) {
    return (
      <Box minH="100vh" bg={bgColor} pt="80px">
        <Flex justify="center" align="center" h="50vh">
          <Spinner size="xl" />
        </Flex>
      </Box>
    )
  }

  if (!selectedWorkflow) {
    return (
      <Box minH="100vh" bg={bgColor} pt="80px">
        <Flex justify="center" align="center" h="50vh">
          <Alert status="error" maxW="md">
            <AlertIcon />
            <Box>
              <AlertTitle>Workflow Not Found</AlertTitle>
              <AlertDescription>
                The requested workflow could not be found.
              </AlertDescription>
            </Box>
          </Alert>
        </Flex>
      </Box>
    )
  }

  return (
    <Box h="100vh" w="100%" position="fixed" top="0" left="0" right="0" bottom="0">
      {/* Header with Back Button */}
      <Flex
        h="72px"
        bg={useColorModeValue('white', 'gray.800')}
        borderBottom="1px"
        borderColor={borderColor}
        align="center"
        px={4}
        zIndex={1001}
      >
        <HStack spacing={3}>
          <Tooltip label="Back to Home">
            <IconButton
              icon={<FiArrowLeft />}
              variant="ghost"
              onClick={() => navigate('/')}
              aria-label="Back to home"
            />
          </Tooltip>
          <Text fontSize="lg" fontWeight="semibold">
            {selectedWorkflow?.name || 'Workflow'}
          </Text>
        </HStack>
      </Flex>

      {/* Main Content */}
      <Flex h="calc(100vh - 72px)" w="100%">
        {/* Left Sidebar - RBI Documents */}
        <Sidebar 
          onDocumentSelect={handleDocumentSelect}
          selectedDoc={selectedDoc}
          onDocumentsUpdate={handleDocumentsUpdate}
        />

        {/* Main Chat Interface */}
        <WorkflowChatInterface 
          selectedWorkflow={selectedWorkflow}
          selectedDoc={selectedDoc}
          onDocumentSelect={handleDocumentSelect}
          onToggleRightSidebar={toggleRightSidebar}
          isRightSidebarOpen={isRightSidebarOpen}
          workflowDocuments={workflowDocuments}
        />

        {/* Right Sidebar - Workflow Documents */}
        <WorkflowRightSidebar 
          selectedWorkflow={selectedWorkflow}
          onDocumentSelect={handleWorkflowDocumentSelect}
          selectedDoc={selectedDoc}
          isOpen={isRightSidebarOpen}
          onToggle={toggleRightSidebar}
          onDocumentsUpdate={setWorkflowDocuments}
        />
      </Flex>
    </Box>
  )
}

export default WorkflowsPage
