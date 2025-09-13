import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  VStack,
  HStack,
  Text,
  Input,
  Textarea,
  FormControl,
  FormLabel,
  Box,
  Badge,
  Flex,
  IconButton,
  Spinner,
  useToast,
  Divider,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
} from '@chakra-ui/react'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiPlus, FiFolder, FiCalendar, FiUser, FiTrash2 } from 'react-icons/fi'

const WorkflowDialog = ({ isOpen, onClose, userId = "default_user" }) => {
  const [workflows, setWorkflows] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    description: ''
  })
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [workflowToDelete, setWorkflowToDelete] = useState(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  
  const toast = useToast()
  const navigate = useNavigate()
  const bgColor = useColorModeValue('gray.50', 'gray.700')
  const borderColor = useColorModeValue('gray.200', 'gray.600')

  // Fetch existing workflows
  const fetchWorkflows = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/workflows?user_id=${userId}`)
      const data = await response.json()
      
      if (data.status === 'success') {
        setWorkflows(data.data.workflows || [])
      } else {
        throw new Error(data.message || 'Failed to fetch workflows')
      }
    } catch (error) {
      console.error('Error fetching workflows:', error)
      toast({
        title: 'Error',
        description: 'Failed to fetch workflows',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsLoading(false)
    }
  }

  // Create new workflow
  const createWorkflow = async () => {
    if (!newWorkflow.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Workflow name is required',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    try {
      setIsCreating(true)
      const response = await fetch(`${import.meta.env.VITE_API_URL}/workflows`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          name: newWorkflow.name.trim(),
          description: newWorkflow.description.trim() || null
        })
      })

      const data = await response.json()
      
      if (data.status === 'success') {
        const workflowId = data.data.workflow.id
        
        toast({
          title: 'Success',
          description: 'Workflow created successfully',
          status: 'success',
          duration: 3000,
          isClosable: true,
        })
        
        // Reset form, close dialog, and navigate to the specific workflow page
        setNewWorkflow({ name: '', description: '' })
        setShowCreateForm(false)
        onClose()
        navigate(`/workflows/${workflowId}`)
      } else {
        throw new Error(data.detail || 'Failed to create workflow')
      }
    } catch (error) {
      console.error('Error creating workflow:', error)
      toast({
        title: 'Error',
        description: error.message || 'Failed to create workflow',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setIsCreating(false)
    }
  }

  // Delete workflow
  const deleteWorkflow = async () => {
    if (!workflowToDelete) return
    
    setDeleteLoading(true)
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/workflows/${workflowToDelete.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId
        })
      })

      const data = await response.json()
      
      if (response.ok && data.status === 'success') {
        // Remove workflow from local state
        setWorkflows(prev => prev.filter(w => w.id !== workflowToDelete.id))
        
        toast({
          title: 'Success',
          description: 'Workflow deleted successfully',
          status: 'success',
          duration: 3000,
          isClosable: true,
        })
      } else {
        throw new Error(data.detail || 'Failed to delete workflow')
      }
    } catch (error) {
      console.error('Error deleting workflow:', error)
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete workflow',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setDeleteLoading(false)
      setDeleteDialogOpen(false)
      setWorkflowToDelete(null)
    }
  }

  const handleDeleteClick = (workflow, e) => {
    e.stopPropagation()
    setWorkflowToDelete(workflow)
    setDeleteDialogOpen(true)
  }

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false)
    setWorkflowToDelete(null)
  }

  // Load workflows when dialog opens
  useEffect(() => {
    if (isOpen) {
      fetchWorkflows()
    }
  }, [isOpen])

  // Reset form when dialog closes
  useEffect(() => {
    if (!isOpen) {
      setShowCreateForm(false)
      setNewWorkflow({ name: '', description: '' })
    }
  }, [isOpen])

  const formatDate = (dateString) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <Flex align="center" gap={2}>
            <FiFolder />
            Workflows
          </Flex>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack spacing={4} align="stretch">
            {/* Create New Workflow Section */}
            <Box>
              {!showCreateForm ? (
                <Button
                  leftIcon={<FiPlus />}
                  colorScheme="blue"
                  onClick={() => setShowCreateForm(true)}
                  width="100%"
                  size="lg"
                >
                  Create New Workflow
                </Button>
              ) : (
                <Box p={4} bg={bgColor} borderRadius="md" border="1px" borderColor={borderColor}>
                  <VStack spacing={3} align="stretch">
                    <Text fontWeight="semibold" fontSize="md">Create New Workflow</Text>
                    
                    <FormControl isRequired>
                      <FormLabel fontSize="sm">Workflow Name</FormLabel>
                      <Input
                        placeholder="Enter workflow name..."
                        value={newWorkflow.name}
                        onChange={(e) => setNewWorkflow(prev => ({ ...prev, name: e.target.value }))}
                        size="sm"
                      />
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel fontSize="sm">Description (Optional)</FormLabel>
                      <Textarea
                        placeholder="Enter workflow description..."
                        value={newWorkflow.description}
                        onChange={(e) => setNewWorkflow(prev => ({ ...prev, description: e.target.value }))}
                        size="sm"
                        rows={3}
                      />
                    </FormControl>
                    
                    <HStack spacing={2}>
                      <Button
                        colorScheme="blue"
                        onClick={createWorkflow}
                        isLoading={isCreating}
                        loadingText="Creating..."
                        size="sm"
                        flex={1}
                      >
                        Create Workflow
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => setShowCreateForm(false)}
                        size="sm"
                      >
                        Cancel
                      </Button>
                    </HStack>
                  </VStack>
                </Box>
              )}
            </Box>

            <Divider />

            {/* Existing Workflows Section */}
            <Box>
              <Flex justify="space-between" align="center" mb={3}>
                <Text fontWeight="semibold" fontSize="md">Your Workflows</Text>
                <Badge colorScheme="blue" borderRadius="full">
                  {workflows.length}
                </Badge>
              </Flex>

              {isLoading ? (
                <Flex justify="center" p={8}>
                  <Spinner size="lg" />
                </Flex>
              ) : workflows.length === 0 ? (
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  <Box>
                    <AlertTitle fontSize="sm">No workflows found!</AlertTitle>
                    <AlertDescription fontSize="sm">
                      Create your first workflow to get started with document processing and compliance tracking.
                    </AlertDescription>
                  </Box>
                </Alert>
              ) : (
                <VStack spacing={3} align="stretch" maxH="300px" overflowY="auto">
                  {workflows.map((workflow) => (
                    <Box
                      key={workflow.id}
                      p={3}
                      bg={bgColor}
                      borderRadius="md"
                      border="1px"
                      borderColor={borderColor}
                      _hover={{ bg: useColorModeValue('gray.100', 'gray.600') }}
                      cursor="pointer"
                      onClick={() => {
                        onClose()
                        navigate(`/workflows/${workflow.id}`)
                      }}
                    >
                      <VStack align="stretch" spacing={2}>
                        <Flex justify="space-between" align="center">
                          <Text fontWeight="medium" fontSize="sm" noOfLines={1} flex="1">
                            {workflow.name || 'Untitled Workflow'}
                          </Text>
                          <HStack spacing={2}>
                            <HStack spacing={1}>
                              <FiCalendar size={12} />
                              <Text fontSize="xs" color="gray.500">
                                {formatDate(workflow.created_at)}
                              </Text>
                            </HStack>
                            <IconButton
                              icon={<FiTrash2 />}
                              size="xs"
                              variant="ghost"
                              colorScheme="red"
                              onClick={(e) => handleDeleteClick(workflow, e)}
                              aria-label="Delete workflow"
                            />
                          </HStack>
                        </Flex>
                        
                        {workflow.description && (
                          <Text fontSize="xs" color="gray.600" noOfLines={2}>
                            {workflow.description}
                          </Text>
                        )}
                        
                        <Flex justify="space-between" align="center">
                          <HStack spacing={1}>
                            <FiUser size={12} />
                            <Text fontSize="xs" color="gray.500">
                              ID: {workflow.id}
                            </Text>
                          </HStack>
                          <Badge size="sm" colorScheme="green">
                            Active
                          </Badge>
                        </Flex>
                      </VStack>
                    </Box>
                  ))}
                </VStack>
              )}
            </Box>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <Button onClick={onClose}>Close</Button>
        </ModalFooter>
      </ModalContent>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        isOpen={deleteDialogOpen}
        onClose={handleDeleteCancel}
        isCentered
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Delete Workflow
            </AlertDialogHeader>

            <AlertDialogBody>
              Are you sure you want to delete "{workflowToDelete?.name || 'this workflow'}"? 
              This will permanently delete the workflow and all associated documents and chat history. 
              This action cannot be undone.
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button onClick={handleDeleteCancel}>
                Cancel
              </Button>
              <Button 
                colorScheme="red" 
                onClick={deleteWorkflow} 
                ml={3}
                isLoading={deleteLoading}
                loadingText="Deleting..."
              >
                Delete
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Modal>
  )
}

export default WorkflowDialog
