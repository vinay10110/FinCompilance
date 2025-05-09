import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Box,
  VStack,
  HStack,
  IconButton,
  Text,
  useColorModeValue,
  Avatar,
  Flex,
  Textarea,
  Spinner,
  Collapse,
  Button,
  Link,
  Badge,
  useToast,
} from '@chakra-ui/react'
import { FiSend, FiRefreshCcw, FiChevronDown, FiChevronUp, FiExternalLink, FiCheckCircle } from 'react-icons/fi'
import Sidebar from './Sidebar'

const UpdatesPanel = ({ updates, isLoading, onRefresh, onUpdateRead, onDocumentSelect, selectedDoc }) => {
  const [isOpen, setIsOpen] = useState(true)
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const updateBgColor = useColorModeValue('gray.50', 'gray.700')

  return (
    <Box 
      borderBottom="1px" 
      borderColor={borderColor}
      bg={bgColor}
    >
      <HStack justify="space-between" p={4}>
        <HStack>
          <Text fontWeight="bold">Latest RBI Updates</Text>
          {isLoading && <Spinner size="sm" />}
        </HStack>
        <HStack>
          <IconButton
            icon={<FiRefreshCcw />}
            size="sm"
            onClick={onRefresh}
            isLoading={isLoading}
            aria-label="Refresh updates"
          />
          <IconButton
            icon={isOpen ? <FiChevronUp /> : <FiChevronDown />}
            size="sm"
            onClick={() => setIsOpen(!isOpen)}
            aria-label={isOpen ? "Collapse updates" : "Expand updates"}
          />
        </HStack>
      </HStack>

      <Collapse in={isOpen}>
        <VStack align="stretch" p={4} pt={0} spacing={4} maxH="300px" overflowY="auto">
          {updates.length === 0 ? (
            <Text color="gray.500" textAlign="center">No updates available</Text>
          ) : (
            updates.map((update, index) => (
              <Box 
                key={index}
                p={4}
                borderRadius="lg"
                bg={updateBgColor}
                position="relative"
                onClick={() => onDocumentSelect(update)}
                cursor="pointer"
                border={selectedDoc?.press_release_link === update.press_release_link ? '2px solid' : 'none'}
                borderColor={selectedDoc?.press_release_link === update.press_release_link ? 'blue.500' : 'transparent'}
              >
                {update.is_new && (
                  <IconButton
                    size="xs"
                    icon={<FiCheckCircle />}
                    position="absolute"
                    top={2}
                    right={2}
                    onClick={(e) => {
                      e.stopPropagation()
                      onUpdateRead(update.press_release_link)
                    }}
                    aria-label="Mark as read"
                    colorScheme="green"
                    variant="ghost"
                  />
                )}
                <VStack align="stretch" spacing={2}>
                  <Text fontWeight="semibold">{update.title}</Text>
                  {update.date && (
                    <Text fontSize="sm" color="gray.500">
                      Date: {new Date(update.date).toLocaleDateString()}
                    </Text>
                  )}
                  <HStack spacing={4}>
                    <Link 
                      href={update.press_release_link} 
                      isExternal
                      color="blue.500"
                      fontSize="sm"
                    >
                      <HStack>
                        <Text>View Press Release</Text>
                        <FiExternalLink />
                      </HStack>
                    </Link>
                    {update.pdf_link && (
                      <Link 
                        href={update.pdf_link} 
                        isExternal
                        color="blue.500"
                        fontSize="sm"
                      >
                        <HStack>
                          <Text>Download PDF</Text>
                          <FiExternalLink />
                        </HStack>
                      </Link>
                    )}
                  </HStack>
                </VStack>
              </Box>
            ))
          )}
        </VStack>
      </Collapse>
    </Box>
  )
}

const Message = ({ message, isUser }) => {
  const bgColor = useColorModeValue(
    isUser ? 'blue.500' : 'gray.100',
    isUser ? 'blue.500' : 'whiteAlpha.200'
  )
  const textColor = useColorModeValue(
    isUser ? 'white' : 'gray.800',
    isUser ? 'white' : 'whiteAlpha.900'
  )
  const messageBgColor = useColorModeValue(
    message.isUser ? 'transparent' : 'gray.50',
    message.isUser ? 'transparent' : 'gray.800'
  )
  
  const contextBgColor = useColorModeValue('gray.50', 'gray.700')
  const contextTextColor = useColorModeValue('gray.600', 'gray.300')

  return (
    <Box 
      w="100%" 
      bg={messageBgColor}
      py={4}
    >
      <Flex
        maxW="7xl"
        mx="auto"
        px={4}
        justify={isUser ? 'flex-end' : 'flex-start'}
      >
        <Flex 
          maxW="3xl" 
          align="start" 
          gap={3}
          flexDir={isUser ? 'row-reverse' : 'row'}
        >
          <Avatar
            size="sm"
            name={isUser ? 'User' : 'AI Assistant'}
            src={!isUser ? '/vite.svg' : undefined}
            bg={isUser ? 'blue.500' : 'green.500'}
          />
          <VStack align={isUser ? 'flex-end' : 'flex-start'} spacing={2} flex={1}>
            <Box
              bg={bgColor}
              px={6}
              py={4}
              borderRadius="2xl"
              borderTopLeftRadius={!isUser ? 'md' : undefined}
              borderTopRightRadius={isUser ? 'md' : undefined}
              shadow="sm"
              width="100%"
            >
              <Text 
                whiteSpace="pre-wrap" 
                color={textColor}
                fontSize="sm"
                lineHeight="tall"
              >
                {message.content}
              </Text>
            </Box>
            
            {/* Show context if available */}
            {!isUser && message.context && message.context.length > 0 && (
              <Box
                bg={contextBgColor}
                p={4}
                borderRadius="xl"
                width="100%"
                fontSize="xs"
              >
                <Text fontWeight="medium" mb={2} color={contextTextColor}>
                  Relevant Document Excerpts:
                </Text>
                <VStack align="stretch" spacing={3}>
                  {message.context.map((ctx, idx) => (
                    <Box key={idx}>
                      <Text color={contextTextColor}>
                        {ctx.chunk}
                      </Text>
                      {ctx.metadata?.page_number && (
                        <Text color={contextTextColor} mt={1} fontStyle="italic">
                          Page {ctx.metadata.page_number}
                        </Text>
                      )}
                    </Box>
                  ))}
                </VStack>
              </Box>
            )}

            {/* Show summary badge if it's a summary message */}
            {!isUser && message.isSummary && (
              <Badge colorScheme="purple" mt={1}>
                Document Summary
              </Badge>
            )}
          </VStack>
        </Flex>
      </Flex>
    </Box>
  )
}

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      content: "Hello! I'm your AI assistant. I can help you understand RBI documents. Select a document to get started!",
      isUser: false,
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [updates, setUpdates] = useState([])
  const [isUpdatesLoading, setIsUpdatesLoading] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [context, setContext] = useState([])
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const toast = useToast()

  const bgColor = useColorModeValue('white', 'gray.900')
  const inputBgColor = useColorModeValue('white', 'gray.800')
  const loadingBgColor = useColorModeValue('gray.50', 'gray.800')

  const fetchUpdates = useCallback(async () => {
    try {
      setIsUpdatesLoading(true)
      const response = await fetch('/api/updates')
      if (!response.ok) throw new Error('Failed to fetch updates')
      const data = await response.json()
      setUpdates(data.updates)
    } catch (error) {
      console.error('Error fetching updates:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch updates',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsUpdatesLoading(false)
    }
  }, [toast])

  const handleUpdateRead = async (pressReleaseLink) => {
    try {
      const response = await fetch('/api/updates/mark-read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ press_release_link: pressReleaseLink }),
      })
      
      if (!response.ok) throw new Error('Failed to mark update as read')
      
      // Refresh updates after marking as read
      fetchUpdates()
      
    } catch (error) {
      console.error('Error marking update as read:', error)
      toast({
        title: 'Error',
        description: 'Failed to mark update as read',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }

  const handleDocumentSelect = (update) => {
    if (update.doc_id) {
      setSelectedDoc(update)
      setMessages(prev => [
        ...prev,
        {
          content: `Now chatting about: ${update.title}`,
          isUser: false,
          isSystem: true
        }
      ])
    } else {
      toast({
        title: 'Document Not Available',
        description: 'This update does not have an associated document to chat about.',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { content: input, isUser: true }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: input,
          doc_id: selectedDoc?.doc_id
        }),
      })

      if (!response.ok) throw new Error('Failed to get response')

      const data = await response.json()
      
      // Update context and add AI response
      setContext(data.context || [])
      setMessages(prev => [...prev, { 
        content: data.response, 
        isUser: false,
        context: data.context
      }])
    } catch (error) {
      console.error('Error:', error)
      toast({
        title: 'Error',
        description: 'Failed to get response. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
      setMessages(prev => [
        ...prev,
        {
          content: 'Sorry, I encountered an error. Please try again.',
          isUser: false,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSummarize = async () => {
    if (!selectedDoc?.doc_id) return
    
    setIsLoading(true)
    try {
      const response = await fetch('/api/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          doc_ids: [selectedDoc.doc_id]
        }),
      })

      if (!response.ok) throw new Error('Failed to get summary')

      const data = await response.json()
      setMessages(prev => [...prev, { 
        content: data.summaries[0].summary,
        isUser: false,
        isSummary: true
      }])
    } catch (error) {
      console.error('Error:', error)
      toast({
        title: 'Error',
        description: 'Failed to generate summary. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchUpdates()
    // Poll for updates every 5 minutes
    const interval = setInterval(fetchUpdates, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [fetchUpdates])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <Flex h="calc(100vh - 72px)" w="100%" position="fixed" top="72px" left="0" right="0" bottom="0">
      <Sidebar 
        onDocumentSelect={handleDocumentSelect}
        selectedDoc={selectedDoc}
      />

      <Box
        flex="1"
        display="flex"
        flexDirection="column"
        bg={bgColor}
        position="relative"
        overflow="hidden"
        borderLeft="1px"
        borderColor={useColorModeValue('gray.200', 'gray.700')}
      >
        <UpdatesPanel 
          updates={updates}
          isLoading={isUpdatesLoading}
          onRefresh={fetchUpdates}
          onUpdateRead={handleUpdateRead}
          onDocumentSelect={handleDocumentSelect}
          selectedDoc={selectedDoc}
        />

        <Box
          flex="1"
          overflowY="auto"
          w="100%"
          position="relative"
          css={{
            '&::-webkit-scrollbar': {
              width: '4px',
            },
            '&::-webkit-scrollbar-track': {
              width: '6px',
            },
            '&::-webkit-scrollbar-thumb': {
              background: useColorModeValue('gray.300', 'gray.700'),
              borderRadius: '24px',
            },
          }}
        >
          <VStack align="stretch" w="100%" pb={20}>
            {messages.map((message, index) => (
              <Message
                key={index}
                message={message}
                isUser={message.isUser}
              />
            ))}
            {isLoading && (
              <Box
                w="100%" 
                bg={loadingBgColor}
                py={4}
              >
                <Flex maxW="7xl" mx="auto" px={4}>
                  <Flex align="center" gap={3}>
                    <Avatar
                      size="sm"
                      name="AI Assistant"
                      src="/vite.svg"
                      bg="green.500"
                    />
                    <Spinner size="sm" />
                  </Flex>
                </Flex>
              </Box>
            )}
            <div ref={messagesEndRef} />
          </VStack>
        </Box>

        <Box
          position="absolute"
          bottom={0}
          left={0}
          right={0}
          bg={inputBgColor}
          borderTop="1px"
          borderColor={useColorModeValue('gray.200', 'gray.700')}
          p={4}
        >
          <Box
            as="form"
            onSubmit={handleSubmit}
            maxW="7xl"
            mx="auto"
          >
            <VStack spacing={3}>
              {selectedDoc && (
                <HStack w="100%" justify="space-between">
                  <Text fontSize="sm" color="gray.500">
                    Chatting about: {selectedDoc.title}
                  </Text>
                  <Button
                    size="sm"
                    onClick={handleSummarize}
                    isDisabled={isLoading}
                  >
                    Summarize Document
                  </Button>
                </HStack>
              )}
              <HStack w="100%" align="flex-end" spacing={3}>
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={selectedDoc ? "Ask me about this document..." : "Select a document to start chatting..."}
                  resize="none"
                  rows={1}
                  maxRows={5}
                  minH="44px"
                  maxH="200px"
                  p={3}
                  bg={useColorModeValue('gray.100', 'gray.700')}
                  borderRadius="xl"
                  border="none"
                  _focus={{
                    boxShadow: 'none',
                    bg: useColorModeValue('gray.200', 'gray.600'),
                  }}
                  _hover={{
                    bg: useColorModeValue('gray.200', 'gray.600'),
                  }}
                  fontSize="sm"
                  flex="1"
                  isDisabled={!selectedDoc}
                />
                <IconButton
                  type="submit"
                  aria-label="Send message"
                  icon={<FiSend />}
                  colorScheme="blue"
                  isLoading={isLoading}
                  isDisabled={!input.trim() || isLoading || !selectedDoc}
                  size="lg"
                  borderRadius="xl"
                  variant="solid"
                />
              </HStack>
            </VStack>
          </Box>
        </Box>
      </Box>
    </Flex>
  )
}

export default ChatInterface