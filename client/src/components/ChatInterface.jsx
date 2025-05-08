import { useState, useRef, useEffect } from 'react'
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
} from '@chakra-ui/react'
import { FiSend } from 'react-icons/fi'

const Message = ({ message, isUser }) => {
  const bgColor = useColorModeValue(
    isUser ? 'blue.500' : 'gray.100',
    isUser ? 'blue.500' : 'whiteAlpha.200'
  )
  const textColor = useColorModeValue(
    isUser ? 'white' : 'gray.800',
    isUser ? 'white' : 'whiteAlpha.900'
  )

  return (
    <Box 
      w="100%" 
      bg={useColorModeValue(
        message.isUser ? 'transparent' : 'gray.50',
        message.isUser ? 'transparent' : 'gray.800'
      )}
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
            name={isUser ? 'User' : 'AI Supervisor'}
            src={!isUser ? '/vite.svg' : undefined}
            bg={isUser ? 'blue.500' : 'green.500'}
          />
          <Box
            bg={bgColor}
            px={6}
            py={4}
            borderRadius="2xl"
            borderTopLeftRadius={!isUser ? 'md' : undefined}
            borderTopRightRadius={isUser ? 'md' : undefined}
            shadow="sm"
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
        </Flex>
      </Flex>
    </Box>
  )
}

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      content: "Hello! I'm your AI supervisor. How can I help you with compliance today?",
      isUser: false,
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

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
        body: JSON.stringify({ message: input }),
      })

      if (!response.ok) throw new Error('Failed to get response')

      const data = await response.json()
      setMessages(prev => [...prev, { content: data.response, isUser: false }])
    } catch (error) {
      console.error('Error:', error)
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

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const bgColor = useColorModeValue('white', 'gray.900')
  const inputBgColor = useColorModeValue('white', 'gray.800')

  return (
    <Box
      h="calc(100vh - 72px)"
      w="100%"
      display="flex"
      flexDirection="column"
      bg={bgColor}
      position="relative"
    >
      {/* Messages Area */}
      <Box
        flex="1"
        overflowY="auto"
        w="100%"
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
              bg={useColorModeValue('gray.50', 'gray.800')}
              py={4}
            >
              <Flex maxW="7xl" mx="auto" px={4}>
                <Flex align="center" gap={3}>
                  <Avatar
                    size="sm"
                    name="AI Supervisor"
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

      {/* Input Area */}
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
          <HStack align="flex-end" spacing={3}>
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
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
            />
            <IconButton
              type="submit"
              aria-label="Send message"
              icon={<FiSend />}
              colorScheme="blue"
              isLoading={isLoading}
              isDisabled={!input.trim() || isLoading}
              size="lg"
              borderRadius="xl"
              variant="solid"
            />
          </HStack>
        </Box>
      </Box>
    </Box>
  )
}

export default ChatInterface