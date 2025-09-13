import { useState, useRef, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  Flex,
  Avatar,
  useColorModeValue,
  Spinner,
  Alert,
  AlertIcon,
  IconButton,
  Tooltip,
  Badge,
  Divider,
  useDisclosure
} from '@chakra-ui/react'
import { FiSend, FiSidebar, FiFileText, FiUser, FiMessageCircle } from 'react-icons/fi'
import { useUser } from '@clerk/clerk-react'
import DocumentCanvas from './DocumentCanvas'

const WorkflowChatInterface = ({ 
  selectedWorkflow, 
  selectedDoc, 
  onDocumentSelect, 
  onToggleRightSidebar, 
  isRightSidebarOpen,
  workflowDocuments = []
}) => {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentDocument, setCurrentDocument] = useState(null)
  const messagesEndRef = useRef(null)
  const { user } = useUser()
  const { isOpen: isDocumentCanvasOpen, onOpen: onDocumentCanvasOpen, onClose: onDocumentCanvasClose } = useDisclosure()

  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')
  const messageBg = useColorModeValue('gray.50', 'gray.700')
  const userMessageBg = useColorModeValue('blue.500', 'blue.600')

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load chat history when workflow is selected
  useEffect(() => {
    if (selectedWorkflow && user) {
      loadChatHistory()
    }
  }, [selectedWorkflow, user])

  const loadChatHistory = async () => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/workflows/${selectedWorkflow.id}/chat/history?user_id=${user.id}&limit=50`
      )
      const data = await response.json()
      
      if (data.status === 'success' && data.data?.messages?.length > 0) {
        setMessages(data.data.messages)
      } else {
        // Initialize with welcome message if no history
        setMessages([
          {
            id: Date.now(),
            type: 'assistant',
            content: `Welcome to ${selectedWorkflow.name}! I'm here to help you analyze documents and answer questions related to this workflow. ${selectedDoc ? `Currently viewing: ${selectedDoc.title || selectedDoc.doc_type || 'Selected Document'}` : 'Select a document from the sidebar to get started.'}`,
            timestamp: new Date().toISOString()
          }
        ])
      }
    } catch (error) {
      console.error('Error loading chat history:', error)
      // Fallback to welcome message
      setMessages([
        {
          id: Date.now(),
          type: 'assistant',
          content: `Welcome to ${selectedWorkflow.name}! I'm here to help you analyze documents and answer questions related to this workflow.`,
          timestamp: new Date().toISOString()
        }
      ])
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Prepare workflow documents data with pdf_chunks_ prefix
      const doc_ids = workflowDocuments.map(doc => `pdf_chunks_${doc.doc_id}`).filter(Boolean)
      const doc_titles = workflowDocuments.map(doc => doc.title || `${doc.doc_type} Document`).filter(Boolean)

      if (doc_ids.length === 0) {
        throw new Error('No documents available in this workflow for chat')
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/workflows/${selectedWorkflow.id}/chat?user_id=${user?.id || 'anonymous'}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          doc_ids: doc_ids,
          doc_titles: doc_titles
        })
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.response?.content || 'I received your message but couldn\'t generate a response.',
          timestamp: new Date().toISOString(),
          document: data.response?.document || null
        }
        setMessages(prev => [...prev, assistantMessage])
        
        // If there's a document, show the canvas automatically
        if (data.response?.document) {
          setCurrentDocument(data.response.document)
          onDocumentCanvasOpen()
        }
      } else {
        throw new Error(data.message || 'Failed to get response')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `Sorry, I encountered an error: ${error.message}. Please make sure documents are added to this workflow.`,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Flex direction="column" flex="1" bg={bgColor} borderRight="1px" borderColor={borderColor}>
      {/* Header */}
      <Flex
        p={4}
        borderBottom="1px"
        borderColor={borderColor}
        align="center"
        justify="space-between"
        bg={bgColor}
      >
        <VStack align="start" spacing={1}>
          <HStack>
            <FiFileText />
            <Text fontWeight="semibold" fontSize="lg">
              {selectedWorkflow?.name || 'Workflow Chat'}
            </Text>
          </HStack>
          {selectedDoc && (
            <HStack spacing={2}>
              <Badge colorScheme="blue" size="sm">
                {selectedDoc.doc_type || selectedDoc.type || 'Document'}
              </Badge>
              <Text fontSize="sm" color="gray.600" noOfLines={1}>
                {selectedDoc.title || selectedDoc.press_release_link || 'Selected Document'}
              </Text>
            </HStack>
          )}
        </VStack>
        
        <IconButton
          icon={<FiSidebar />}
          variant="ghost"
          onClick={onToggleRightSidebar}
          aria-label="Toggle right sidebar"
        />
      </Flex>

      {/* Messages Area */}
      <Box flex="1" overflowY="auto" p={4}>
        <VStack spacing={4} align="stretch">
          {messages.length === 0 ? (
            <Alert status="info">
              <AlertIcon />
              <Box>
                <Text fontWeight="semibold">Ready to Chat</Text>
                <Text fontSize="sm">
                  Ask me questions about the selected documents or workflow processes.
                </Text>
              </Box>
            </Alert>
          ) : (
            messages.map((message) => (
              <Flex
                key={message.id}
                justify={message.type === 'user' ? 'flex-end' : 'flex-start'}
              >
                <HStack
                  maxW="80%"
                  spacing={3}
                  align="flex-start"
                  flexDirection={message.type === 'user' ? 'row-reverse' : 'row'}
                >
                  <Avatar
                    size="sm"
                    icon={message.type === 'user' ? <FiUser /> : <FiMessageCircle />}
                    bg={message.type === 'user' ? 'blue.500' : 'green.500'}
                  />
                  <Box
                    bg={message.type === 'user' ? userMessageBg : messageBg}
                    color={message.type === 'user' ? 'white' : 'inherit'}
                    p={3}
                    borderRadius="lg"
                    maxW="100%"
                  >
                    <Text fontSize="sm" whiteSpace="pre-wrap">
                      {message.content}
                    </Text>
                    
                    {/* Show document button if message has a document */}
                    {message.document && (
                      <Button
                        size="xs"
                        mt={2}
                        leftIcon={<FiFileText />}
                        colorScheme="blue"
                        variant="outline"
                        onClick={() => {
                          setCurrentDocument(message.document)
                          onDocumentCanvasOpen()
                        }}
                      >
                        View Document
                      </Button>
                    )}
                    
                    <Text
                      fontSize="xs"
                      opacity={0.7}
                      mt={1}
                      textAlign={message.type === 'user' ? 'right' : 'left'}
                    >
                      {formatTime(message.timestamp)}
                    </Text>
                  </Box>
                </HStack>
              </Flex>
            ))
          )}
          
          {isLoading && (
            <Flex justify="flex-start">
              <HStack spacing={3} align="center">
                <Avatar size="sm" icon={<FiMessageCircle />} bg="green.500" />
                <Box bg={messageBg} p={3} borderRadius="lg">
                  <HStack spacing={2}>
                    <Spinner size="sm" />
                    <Text fontSize="sm">Thinking...</Text>
                  </HStack>
                </Box>
              </HStack>
            </Flex>
          )}
          
          <div ref={messagesEndRef} />
        </VStack>
      </Box>

      {/* Input Area */}
      <Box p={4} borderTop="1px" borderColor={borderColor} bg={bgColor}>
        <HStack spacing={3}>
          <Input
            placeholder={
              selectedDoc 
                ? `Ask about ${selectedDoc.title || selectedDoc.doc_type || 'this document'}...`
                : "Ask about workflow or select a document..."
            }
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            bg={useColorModeValue('white', 'gray.700')}
          />
          <Button
            colorScheme="blue"
            onClick={handleSendMessage}
            isLoading={isLoading}
            disabled={!inputValue.trim()}
            leftIcon={<FiSend />}
          >
            Send
          </Button>
        </HStack>
      </Box>

      {/* Document Canvas */}
      <DocumentCanvas
        isOpen={isDocumentCanvasOpen}
        onClose={onDocumentCanvasClose}
        document={currentDocument}
        title="Generated Compliance Document"
      />
    </Flex>
  )
}

export default WorkflowChatInterface
