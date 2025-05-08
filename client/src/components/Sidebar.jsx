import {
  Box,
  VStack,
  Text,
  useColorModeValue,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Badge,
  Link,
  Flex,
  IconButton,
  Spinner,
  Tooltip,
  useToast,
  HStack,
} from '@chakra-ui/react'
import { FiExternalLink, FiRefreshCcw, FiDownload, FiCheck, FiBell } from 'react-icons/fi'
import { useState, useEffect } from 'react'

const UpdateItem = ({ update, onMarkRead }) => {
  const bgColor = useColorModeValue('gray.50', 'gray.700')
  const [isMarking, setIsMarking] = useState(false)
  
  const handleMarkRead = async () => {
    try {
      setIsMarking(true)
      await onMarkRead(update.press_release_link)
    } finally {
      setIsMarking(false)
    }
  }
  
  return (
    <Box
      p={3}
      bg={bgColor}
      borderRadius="md"
      _hover={{ bg: useColorModeValue('gray.100', 'gray.600') }}
    >
      <VStack align="stretch" spacing={2}>
        <Flex justify="space-between" align="start" gap={2}>
          <Text fontSize="sm" fontWeight="medium" noOfLines={2}>
            {update.title}
          </Text>
          {update.is_new && (
            <IconButton
              size="xs"
              icon={isMarking ? <Spinner size="xs" /> : <FiCheck />}
              onClick={handleMarkRead}
              aria-label="Mark as read"
              variant="ghost"
              colorScheme="green"
              isDisabled={isMarking}
            />
          )}
        </Flex>
        
        <Text fontSize="xs" color="gray.500">
          {new Date(update.date_published || update.date_scraped).toLocaleDateString()}
        </Text>
        
        <Flex gap={2} fontSize="xs">
          <Link 
            href={update.press_release_link} 
            isExternal 
            color="blue.500"
            display="inline-flex"
            alignItems="center"
            gap={1}
          >
            View <FiExternalLink />
          </Link>
          
          {update.pdf_link && (
            <Link 
              href={update.pdf_link} 
              isExternal
              color="blue.500"
              display="inline-flex"
              alignItems="center"
              gap={1}
            >
              PDF <FiDownload />
            </Link>
          )}
        </Flex>
      </VStack>
    </Box>
  )
}

const Sidebar = () => {
  const [updates, setUpdates] = useState({ new: [], previous: [] })
  const [isLoading, setIsLoading] = useState(false)
  const [hasNewUpdates, setHasNewUpdates] = useState(false)
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const toast = useToast()
  
  const fetchUpdates = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/updates')
      if (!response.ok) throw new Error('Failed to fetch updates')
      const data = await response.json()
      
      // Split updates into new and previous
      const newUpdates = data.updates.filter(u => u.is_new)
      const previousUpdates = data.updates.filter(u => !u.is_new)
      
      setUpdates({
        new: newUpdates,
        previous: previousUpdates
      })
      
      // Set notification state if there are new updates
      setHasNewUpdates(newUpdates.length > 0)
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
      setIsLoading(false)
    }
  }

  // Poll for updates every 5 minutes
  useEffect(() => {
    fetchUpdates()
    const interval = setInterval(fetchUpdates, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [fetchUpdates])

  const handleMarkRead = async (pressReleaseLink) => {
    try {
      const response = await fetch('/api/updates/mark-read', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ press_release_link: pressReleaseLink }),
      })
      
      if (!response.ok) throw new Error('Failed to mark update as read')
      
      // Refresh updates
      await fetchUpdates()
      
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

  return (
    <Box
      w="300px"
      h="100%"
      borderRight="1px"
      borderColor={borderColor}
      bg={useColorModeValue('white', 'gray.800')}
      position="relative"
      overflow="hidden"
      display="flex"
      flexDirection="column"
      flexShrink={0}
    >
      <Flex justify="space-between" align="center" p={4} borderBottom="1px" borderColor={borderColor}>
        <Text fontWeight="bold">RBI Updates</Text>
        <HStack spacing={2}>
          {hasNewUpdates && (
            <IconButton
              size="sm"
              icon={<FiBell />}
              colorScheme="red"
              variant="ghost"
              aria-label="New updates"
            />
          )}
          <Tooltip label="Refresh updates">
            <IconButton
              size="sm"
              icon={isLoading ? <Spinner size="sm" /> : <FiRefreshCcw />}
              onClick={fetchUpdates}
              isLoading={isLoading}
              aria-label="Refresh updates"
            />
          </Tooltip>
        </HStack>
      </Flex>

      <Tabs>
        <TabList px={4}>
          <Tab>
            New{' '}
            {updates.new.length > 0 && (
              <Badge ml={2} colorScheme="red" borderRadius="full">
                {updates.new.length}
              </Badge>
            )}
          </Tab>
          <Tab>Previous</Tab>
        </TabList>

        <TabPanels>
          <TabPanel p={4}>
            <VStack align="stretch" spacing={3}>
              {updates.new.length === 0 ? (
                <Text color="gray.500" fontSize="sm" textAlign="center">
                  No new updates
                </Text>
              ) : (
                updates.new.map((update, index) => (
                  <UpdateItem 
                    key={index} 
                    update={update}
                    onMarkRead={handleMarkRead}
                  />
                ))
              )}
            </VStack>
          </TabPanel>
          
          <TabPanel p={4}>
            <VStack align="stretch" spacing={3} maxH="calc(100vh - 200px)" overflowY="auto">
              {updates.previous.length === 0 ? (
                <Text color="gray.500" fontSize="sm" textAlign="center">
                  No previous updates
                </Text>
              ) : (
                updates.previous.map((update, index) => (
                  <UpdateItem 
                    key={index} 
                    update={update}
                    onMarkRead={handleMarkRead}
                  />
                ))
              )}
            </VStack>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}

export default Sidebar