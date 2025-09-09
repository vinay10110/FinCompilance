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
  Select,
  Input,
  InputGroup,
  InputLeftElement,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  useDisclosure,
} from '@chakra-ui/react'
import { FiExternalLink, FiRefreshCcw, FiDownload, FiCheck, FiBell, FiFileText, FiSearch, FiPlus } from 'react-icons/fi'
import { useState, useEffect, useCallback } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { useUser } from '@clerk/clerk-react'

const UpdateItem = ({ update, onSelect, isSelected, type = 'press_release', isOnWorkflowPage, onAddToWorkflow }) => {
  const bgColor = useColorModeValue('gray.50', 'gray.700')
  const { isOpen, onOpen, onClose } = useDisclosure()
  
  const handleItemClick = () => {
    if (isOnWorkflowPage) {
      onOpen()
    } else {
      onSelect(update)
    }
  }
  
  const handleAddToWorkflow = () => {
    onAddToWorkflow(update, type)
    onClose()
  }
  
  return (
    <>
      <Box
        p={3}
        bg={bgColor}
        borderRadius="md"
        _hover={{ bg: useColorModeValue('gray.100', 'gray.600') }}
        cursor="pointer"
        onClick={handleItemClick}
        position="relative"
        border={isSelected ? "2px solid" : "none"}
        borderColor="blue.500"
      >
        <VStack align="stretch" spacing={2}>
          <Text fontSize="sm" fontWeight="medium" noOfLines={2}>
            {update.title}
          </Text>
          
          {type === 'circular' && update.category && (
            <Badge colorScheme="blue" fontSize="xs" w="fit-content">
              {update.category}
            </Badge>
          )}
          
          <Text fontSize="xs" color="gray.500">
            {new Date(update.date_published || update.date_scraped).toLocaleDateString()}
          </Text>
          
          <Flex gap={2} fontSize="xs">
            {type === 'press_release' ? (
              <>
                <Link 
                  href={update.press_release_link} 
                  isExternal 
                  color="blue.500"
                  display="inline-flex"
                  alignItems="center"
                  gap={1}
                  onClick={(e) => e.stopPropagation()}
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
                    onClick={(e) => e.stopPropagation()}
                  >
                    PDF <FiDownload />
                  </Link>
                )}
              </>
            ) : (
              <Link 
                href={update.pdf_link} 
                isExternal
                color="blue.500"
                display="inline-flex"
                alignItems="center"
                gap={1}
                onClick={(e) => e.stopPropagation()}
              >
                View Circular <FiFileText />
              </Link>
            )}
          </Flex>
        </VStack>
      </Box>

      {/* Add to Workflow Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Add to Workflow</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack align="stretch" spacing={3}>
              <Text fontSize="sm" fontWeight="medium">
                {update.title}
              </Text>
              <Text fontSize="xs" color="gray.600">
                Do you want to add this {type === 'press_release' ? 'press release' : 'circular'} to your current workflow?
              </Text>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" leftIcon={<FiPlus />} onClick={handleAddToWorkflow}>
              Add to Workflow
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  )
}

const Sidebar = ({ onDocumentSelect, selectedDoc }) => {
  const [updates, setUpdates] = useState({ new: [], previous: [] })
  const [circulars, setCirculars] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingCirculars, setIsLoadingCirculars] = useState(false)
  const [hasNewUpdates, setHasNewUpdates] = useState(false)
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const toast = useToast()
  const location = useLocation()
  const { workflowId } = useParams()
  const { user } = useUser()
  
  // Check if we're on a workflow page
  const isOnWorkflowPage = location.pathname.startsWith('/workflows/')
  
  // Handle adding document to workflow
  const handleAddToWorkflow = async (update, type) => {
    if (!workflowId || !user) {
      toast({
        title: 'Error',
        description: 'Unable to add document to workflow',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/workflows/${workflowId}/documents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          doc_type: type,
          doc_id: update.doc_id
        })
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        toast({
          title: 'Success',
          description: 'Document vectorized and added to workflow successfully',
          status: 'success',
          duration: 4000,
          isClosable: true,
        })
      } else {
        throw new Error(data.message || 'Failed to add document to workflow')
      }
    } catch (error) {
      console.error('Error adding document to workflow:', error)
      toast({
        title: 'Error',
        description: error.message || 'Failed to add document to workflow',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    }
  }
  
  const fetchUpdates = useCallback(async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/get_updates`)
      if (!response.ok) throw new Error('Failed to fetch updates')
      const data = await response.json()
      if (data.status === 'success' && Array.isArray(data.updates)) {
        // Get today's date in YYYY-MM-DD format
        const today = new Date().toISOString().split('T')[0]
        
        // Split updates based on today's date
        const todayUpdates = data.updates.filter(u => {
          const updateDate = new Date(u.date_published || u.date_scraped).toISOString().split('T')[0]
          return updateDate === today
        })
        const previousUpdates = data.updates.filter(u => {
          const updateDate = new Date(u.date_published || u.date_scraped).toISOString().split('T')[0]
          return updateDate !== today
        })
        
        setUpdates({
          new: todayUpdates,
          previous: previousUpdates
        })
        
        // Set notification state if there are today's updates
        setHasNewUpdates(todayUpdates.length > 0)
      } else {
        throw new Error('Invalid response format')
      }
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
  }, [toast])

  const fetchCirculars = useCallback(async () => {
    try {
      setIsLoadingCirculars(true)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/get_circulars`)
      if (!response.ok) throw new Error('Failed to fetch circulars')
      const data = await response.json()
      if (data.status === 'success' && Array.isArray(data.updates)) {
        setCirculars(data.updates)
      } else {
        throw new Error('Invalid response format')
      }
    } catch (error) {
      console.error('Error fetching circulars:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch circulars',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoadingCirculars(false)
    }
  }, [toast])

  // Initial fetch on component mount
  useEffect(() => {
    fetchUpdates()
    fetchCirculars()
  }, [fetchUpdates, fetchCirculars])

  // Get unique categories from circulars
  const categories = ['all', ...new Set(circulars.map(c => c.category).filter(Boolean))]
  
  // Filter circulars by selected category and search query
  const filteredCirculars = circulars
    .filter(c => selectedCategory === 'all' || c.category === selectedCategory)
    .filter(c => searchQuery === '' || c.title.toLowerCase().includes(searchQuery.toLowerCase()))

  // Filter press releases by search query
  const filteredNewUpdates = updates.new.filter(u => 
    searchQuery === '' || u.title.toLowerCase().includes(searchQuery.toLowerCase())
  )
  const filteredPreviousUpdates = updates.previous.filter(u => 
    searchQuery === '' || u.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

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
      <VStack spacing={3} p={4} borderBottom="1px" borderColor={borderColor}>
        <Flex justify="space-between" align="center" w="100%">
          <Text fontWeight="bold">RBI Documents</Text>
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
            <Tooltip label="Refresh data">
              <IconButton
                size="sm"
                icon={isLoading || isLoadingCirculars ? <Spinner size="sm" /> : <FiRefreshCcw />}
                onClick={() => {
                  fetchUpdates()
                  fetchCirculars()
                }}
                isLoading={isLoading || isLoadingCirculars}
                aria-label="Refresh data"
              />
            </Tooltip>
          </HStack>
        </Flex>
        
        <InputGroup size="sm">
          <InputLeftElement pointerEvents="none">
            <FiSearch color="gray.300" />
          </InputLeftElement>
          <Input
            placeholder="Search updates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg={useColorModeValue('gray.50', 'gray.700')}
            border="none"
            _focus={{
              bg: useColorModeValue('white', 'gray.600'),
              boxShadow: 'sm'
            }}
          />
        </InputGroup>
      </VStack>

      <Tabs>
        <TabList px={4}>
          <Tab>
            Circulars{' '}
            {filteredCirculars.length > 0 && (
              <Badge ml={2} colorScheme="blue" borderRadius="full">
                {filteredCirculars.length}
              </Badge>
            )}
          </Tab>
          <Tab>
            Press Releases{' '}
            {(filteredNewUpdates.length + filteredPreviousUpdates.length) > 0 && (
              <Badge ml={2} colorScheme="green" borderRadius="full">
                {filteredNewUpdates.length + filteredPreviousUpdates.length}
              </Badge>
            )}
          </Tab>
        </TabList>

        <TabPanels>
          <TabPanel p={4}>
            <VStack align="stretch" spacing={3}>
              <Select
                size="sm"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                placeholder="Filter by category"
              >
                {categories.map(category => (
                  <option key={category} value={category}>
                    {category === 'all' ? 'All Categories' : category}
                  </option>
                ))}
              </Select>
              
              <VStack align="stretch" spacing={3} maxH="calc(100vh - 280px)" overflowY="auto">
                {isLoadingCirculars ? (
                  <Flex justify="center" p={4}>
                    <Spinner />
                  </Flex>
                ) : filteredCirculars.length === 0 ? (
                  <Text color="gray.500" fontSize="sm" textAlign="center">
                    {searchQuery ? 'No matching circulars found' : 'No circulars found'}
                  </Text>
                ) : (
                  filteredCirculars.map((circular, index) => (
                    <UpdateItem 
                      key={index} 
                      update={circular}
                      onSelect={onDocumentSelect}
                      isSelected={selectedDoc?.pdf_link === circular.pdf_link}
                      type="circular"
                      isOnWorkflowPage={isOnWorkflowPage}
                      onAddToWorkflow={handleAddToWorkflow}
                    />
                  ))
                )}
              </VStack>
            </VStack>
          </TabPanel>
          
          <TabPanel p={4}>
            <Tabs size="sm" variant="soft-rounded">
              <TabList>
                <Tab fontSize="xs">
                  Today{' '}
                  {filteredNewUpdates.length > 0 && (
                    <Badge ml={1} colorScheme="red" borderRadius="full" fontSize="xs">
                      {filteredNewUpdates.length}
                    </Badge>
                  )}
                </Tab>
                <Tab fontSize="xs">Previous</Tab>
              </TabList>
              
              <TabPanels>
                <TabPanel p={2}>
                  <VStack align="stretch" spacing={3} maxH="calc(100vh - 320px)" overflowY="auto">
                    {filteredNewUpdates.length === 0 ? (
                      <Text color="gray.500" fontSize="sm" textAlign="center">
                        {searchQuery ? 'No matching updates found' : 'No updates today'}
                      </Text>
                    ) : (
                      filteredNewUpdates.map((update, index) => (
                        <UpdateItem 
                          key={index} 
                          update={update}
                          onSelect={onDocumentSelect}
                          isSelected={selectedDoc?.press_release_link === update.press_release_link}
                          type="press_release"
                          isOnWorkflowPage={isOnWorkflowPage}
                          onAddToWorkflow={handleAddToWorkflow}
                        />
                      ))
                    )}
                  </VStack>
                </TabPanel>
                
                <TabPanel p={2}>
                  <VStack align="stretch" spacing={3} maxH="calc(100vh - 320px)" overflowY="auto">
                    {filteredPreviousUpdates.length === 0 ? (
                      <Text color="gray.500" fontSize="sm" textAlign="center">
                        {searchQuery ? 'No matching updates found' : 'No previous updates'}
                      </Text>
                    ) : (
                      filteredPreviousUpdates.map((update, index) => (
                        <UpdateItem 
                          key={index} 
                          update={update}
                          onSelect={onDocumentSelect}
                          isSelected={selectedDoc?.press_release_link === update.press_release_link}
                          type="press_release"
                          isOnWorkflowPage={isOnWorkflowPage}
                          onAddToWorkflow={handleAddToWorkflow}
                        />
                      ))
                    )}
                  </VStack>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}

export default Sidebar