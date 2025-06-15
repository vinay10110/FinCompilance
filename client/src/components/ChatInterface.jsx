import { useState, useRef, useEffect, useCallback } from 'react'
import { useUser } from "@clerk/clerk-react"
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
  Button,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  Badge,
} from '@chakra-ui/react'
import { FiSend, FiDownload } from 'react-icons/fi'
import Sidebar from './Sidebar'

const Message = ({ message, isUser, onOpenDocument }) => {
  const bgColor = useColorModeValue(
    isUser ? 'blue.500' : message.isSystem ? 'blue.50' : 'gray.100',
    isUser ? 'blue.500' : message.isSystem ? 'blue.900' : 'whiteAlpha.200'
  )
  const textColor = useColorModeValue(
    isUser ? 'white' : message.isSystem ? 'blue.600' : 'gray.800',
    isUser ? 'white' : message.isSystem ? 'blue.200' : 'whiteAlpha.900'
  )
  const messageBgColor = useColorModeValue(
    message.isUser ? 'transparent' : message.isSystem ? 'blue.50' : 'gray.50',
    message.isUser ? 'transparent' : message.isSystem ? 'blue.900' : 'gray.800'
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
              >                <Text fontWeight="medium" mb={2} color={contextTextColor}>
                  Relevant Document Excerpts:
                </Text>
                <Box>
                  <Text color={contextTextColor} whiteSpace="pre-wrap">
                    {message.context}
                  </Text>
                </Box>
              </Box>
            )}            {/* Show badges for different message types */}
            {!isUser && (message.isSummary || message.isDocument) && (
              <HStack spacing={2} mt={1}>
                {message.isSummary && (
                  <Badge colorScheme="purple">Document Summary</Badge>
                )}
                {message.isDocument && (                  <Badge colorScheme="green" cursor="pointer" onClick={onOpenDocument}>
                    View Generated Document
                  </Badge>
                )}
              </HStack>
            )}
          </VStack>
        </Flex>
      </Flex>
    </Box>
  )
}

const ChatInterface = () => {
  const { user } = useUser();
  const [messages, setMessages] = useState([
    {
      content: "Hello! I'm your AI assistant. I can help you understand RBI documents and create summaries or reports. Select a document to get started!",
      isUser: false,
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [isDocumentEditorOpen, setIsDocumentEditorOpen] = useState(false)
  const [documentContent, setDocumentContent] = useState('')
  const [documentTitle, setDocumentTitle] = useState('')
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)
  const toast = useToast()

  const bgColor = useColorModeValue('white', 'gray.900')
  const inputBgColor = useColorModeValue('white', 'gray.800')
  const loadingBgColor = useColorModeValue('gray.50', 'gray.800')
  const [showPullDialog, setShowPullDialog] = useState(false)
  const [pendingDoc, setPendingDoc] = useState(null);
  
  const fetchChatHistory = useCallback(async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`http://localhost:5000/getchats?user_id=${encodeURIComponent(user.id)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) throw new Error('Failed to fetch chat history');

      const data = await response.json();
      
      if (!data.messages || data.messages.length === 0) {
        setMessages([{
          content: "No previous chat history found. How can I help you today?",
          isUser: false
        }]);
        return;
      }      // Replace initial message with chat history in correct order
      const sortedMessages = [...data.messages].reverse(); // Reverse to show oldest first
      setMessages(sortedMessages.map(msg => ({
        content: msg.content,
        isUser: msg.isUser || msg.message_type === 'user'  // Handle both formats
      })));
    } catch (error) {
      console.error('Error fetching chat history:', error);
      toast({
        title: 'Note',
        description: 'Starting a new chat session.',
        status: 'info',
        duration: 5000,
        isClosable: true,
      });
      // Set default welcome message
      setMessages([{
        content: "Hello! I'm your AI assistant. I can help you understand RBI documents and create summaries or reports. Select a document to get started!",
        isUser: false
      }]);
    }
  }, [user, toast, setMessages]);

  const handleDocumentSelect = (update) => {
    if (update.doc_id) {
      setPendingDoc(update)
      setShowPullDialog(true)
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
  const handlePullAndChat = async () => {
    if (!pendingDoc) return
    
    // Update selected document
    setSelectedDoc(pendingDoc)
    
    // Add system message about new document while preserving history
    setMessages(prev => [
      ...prev,
      {
        content: `Switched to document: ${pendingDoc.title}`,
        isUser: false,
        isSystem: true,
        highlight: true // Can be used for styling if needed
      }
    ])// Process and store the document
    setIsLoading(true)
    try {
      // Call /vectorize to process the document
      const vectorizeResponse = await fetch('http://localhost:5000/vectorize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          doc_id: pendingDoc.doc_id,
          pdf_link: pendingDoc.pdf_link
        }),
      })

      if (!vectorizeResponse.ok) throw new Error('Failed to process document')
      
      // Show success message
      toast({
        title: 'Document Ready',
        description: 'You can now start chatting about this document.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      })
    } catch (error) {
      console.error('Error:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch document overview.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
      setShowPullDialog(false)
      setPendingDoc(null)
    }
  }

  const handleCancelPull = () => {
    setShowPullDialog(false)
    setPendingDoc(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (!user) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to use the chat feature.',
        status: 'warning',
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    const userMessage = { content: input, isUser: true };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
        const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: input,
          doc_id: selectedDoc?.doc_id,
          user_id: user.id
        }),
      });
      
      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();
      
      if (data.document) {
        setDocumentContent(data.document.content);
        setDocumentTitle(data.document.title || 'Generated Document');
        setIsDocumentEditorOpen(true);
        setMessages(prev => [...prev, {
          content: 'I have generated a document for you. You can view and download it.',
          isUser: false,
          isDocument: true
        }]);      } else {
        setMessages(prev => [...prev, {
          content: data.response.content,
          isUser: false,
          context: data.response.context
        }]);
      }
    } catch (error) {
      console.error('Error:', error);
      toast({
        title: 'Error',
        description: 'Failed to get response. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      setMessages(prev => [
        ...prev,
        {
          content: 'Sorry, I encountered an error. Please try again.',
          isUser: false,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  useEffect(() => {
    if (user) {
      fetchChatHistory();
    }
  }, [user, fetchChatHistory]);

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
            {messages.map((message, index) => (              <Message
                key={index}
                message={message}
                isUser={message.isUser}
                onOpenDocument={() => setIsDocumentEditorOpen(true)}
              />
            ))}
            {messages.length === 1 && (
              <Box p={8} textAlign="center">
                <Text color="gray.500" fontSize="sm">
                  You can ask me to:
                  <br />
                  • Chat about the document
                  <br />
                  • Create a summary
                  <br />
                  • Generate a report or analysis
                </Text>
              </Box>
            )}
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
        </Box>        <Modal isOpen={isDocumentEditorOpen} onClose={() => setIsDocumentEditorOpen(false)} size="4xl">
          <ModalOverlay />
          <ModalContent>
            <ModalHeader>{documentTitle}</ModalHeader>
            <ModalCloseButton />
            <ModalBody>
              <Box 
                p={4} 
                bg={useColorModeValue('gray.50', 'gray.700')} 
                borderRadius="md"
                whiteSpace="pre-wrap"
                maxH="60vh"
                overflowY="auto"
              >
                {documentContent}
              </Box>
            </ModalBody>
            <ModalFooter>
              <Button
                leftIcon={<FiDownload />}
                colorScheme="blue"
                onClick={() => {
                  const blob = new Blob([documentContent], { type: 'text/plain' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${documentTitle}.txt`;
                  a.click();
                }}
              >
                Download Document
              </Button>
            </ModalFooter>
          </ModalContent>
        </Modal>

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
                </HStack>
              )}
              <HStack w="100%" align="flex-end" spacing={3}>                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isLoading 
                      ? "Processing document..." 
                      : selectedDoc 
                        ? "Ask me about this document..." 
                        : "Select a document to start chatting..."
                  }
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
                  isDisabled={!selectedDoc || isLoading}
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

      {/* Confirmation Dialog for Pull & Chat */}
      <Modal isOpen={showPullDialog} onClose={handleCancelPull}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Confirm Document Selection</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              {pendingDoc?.title}
            </Text>
            <Text mt={2} fontSize="sm" color="gray.500">
              The document will be processed and made available for chat. This might take a moment.
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={handleCancelPull}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handlePullAndChat} isLoading={isLoading}>
              Pull & Chat
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Flex>
  )
}

export default ChatInterface