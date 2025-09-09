import { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Flex,
  IconButton,
  useColorModeValue,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Badge,
  Tooltip,
  Divider,
  Input,
  InputGroup,
  InputLeftElement,
  Collapse,
  useDisclosure,
  Link
} from '@chakra-ui/react'
import { 
  FiX, 
  FiFileText, 
  FiCalendar, 
  FiSearch, 
  FiPlus,
  FiFolder,
  FiChevronDown,
  FiChevronRight,
  FiUpload,
  FiExternalLink,
  FiDownload
} from 'react-icons/fi'
import { useUser } from '@clerk/clerk-react'

const WorkflowRightSidebar = ({ 
  selectedWorkflow, 
  onDocumentSelect, 
  selectedDoc, 
  isOpen, 
  onToggle,
  onDocumentsUpdate 
}) => {
  const [workflowDocuments, setWorkflowDocuments] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const { user } = useUser()
  const { isOpen: isDocumentsOpen, onToggle: onDocumentsToggle } = useDisclosure({ defaultIsOpen: true })

  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')
  const hoverBg = useColorModeValue('gray.50', 'gray.700')
  const selectedBg = useColorModeValue('blue.50', 'blue.900')

  // Fetch workflow documents
  useEffect(() => {
    if (selectedWorkflow && isOpen) {
      fetchWorkflowDocuments()
    }
  }, [selectedWorkflow, isOpen])

  // Update parent component when documents change
  useEffect(() => {
    if (onDocumentsUpdate) {
      onDocumentsUpdate(workflowDocuments)
    }
  }, [workflowDocuments, onDocumentsUpdate])

  const fetchWorkflowDocuments = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/workflows/${selectedWorkflow.id}`
      )
      const data = await response.json()
      
      if (data.status === 'success') {
        const workflow = data.data.workflow
        const workflowDocs = workflow.documents || []
        
        // Fetch full document details for each workflow document using the new API route
        const documentsWithDetails = await Promise.all(
          workflowDocs.map(async (workflowDoc) => {
            try {
              const docResponse = await fetch(
                `${import.meta.env.VITE_API_URL}/documents/${workflowDoc.doc_type}/${workflowDoc.doc_id}`
              )
              
              if (docResponse.ok) {
                const docData = await docResponse.json()
                if (docData.status === 'success') {
                  return {
                    ...docData.data.document,
                    workflow_doc_type: workflowDoc.doc_type,
                    added_at: workflowDoc.added_at
                  }
                }
              }
              
              // Fallback if document not found
              return {
                id: workflowDoc.doc_id,
                doc_id: workflowDoc.doc_id,
                title: `Document ID: ${workflowDoc.doc_id}`,
                doc_type: workflowDoc.doc_type,
                workflow_doc_type: workflowDoc.doc_type,
                added_at: workflowDoc.added_at,
                date_published: workflowDoc.added_at
              }
            } catch (error) {
              console.error('Error fetching document details:', error)
              return {
                id: workflowDoc.doc_id,
                doc_id: workflowDoc.doc_id,
                title: `Document ID: ${workflowDoc.doc_id}`,
                doc_type: workflowDoc.doc_type,
                workflow_doc_type: workflowDoc.doc_type,
                added_at: workflowDoc.added_at,
                date_published: workflowDoc.added_at
              }
            }
          })
        )
        
        setWorkflowDocuments(documentsWithDetails)
        // Update parent component with documents for chat interface
        if (onDocumentsUpdate) {
          onDocumentsUpdate(documentsWithDetails)
        }
        console.log('✅ Workflow documents loaded:', documentsWithDetails)
      } else {
        console.error('Failed to fetch workflow documents:', data.message)
      }
    } catch (error) {
      console.error('❌ Error fetching workflow documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredDocuments = workflowDocuments.filter(doc =>
    doc.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.doc_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doc.doc_id?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown'
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const handleDocumentClick = (document) => {
    onDocumentSelect(document)
  }

  if (!isOpen) {
    return null
  }

  return (
    <Box
      w="350px"
      h="100%"
      bg={bgColor}
      borderLeft="1px"
      borderColor={borderColor}
      display="flex"
      flexDirection="column"
    >
      {/* Header */}
      <Flex
        p={4}
        borderBottom="1px"
        borderColor={borderColor}
        align="center"
        justify="space-between"
      >
        <HStack spacing={2}>
          <FiFolder />
          <Text fontWeight="semibold" fontSize="md">
            Workflow Documents
          </Text>
        </HStack>
        <Tooltip label="Close sidebar">
          <IconButton
            icon={<FiX />}
            size="sm"
            variant="ghost"
            onClick={onToggle}
            aria-label="Close sidebar"
          />
        </Tooltip>
      </Flex>

      {/* Workflow Info */}
      {selectedWorkflow && (
        <Box p={4} borderBottom="1px" borderColor={borderColor}>
          <VStack align="stretch" spacing={2}>
            <Text fontSize="sm" fontWeight="medium" noOfLines={2}>
              {selectedWorkflow.name}
            </Text>
            {selectedWorkflow.description && (
              <Text fontSize="xs" color="gray.600" noOfLines={3}>
                {selectedWorkflow.description}
              </Text>
            )}
            <HStack justify="space-between" fontSize="xs" color="gray.500">
              <HStack>
                <FiCalendar />
                <Text>Created {formatDate(selectedWorkflow.created_at)}</Text>
              </HStack>
              <Badge size="sm" colorScheme="green">
                Active
              </Badge>
            </HStack>
          </VStack>
        </Box>
      )}

      {/* Search */}
      <Box p={4}>
        <InputGroup size="sm">
          <InputLeftElement pointerEvents="none">
            <FiSearch color="gray.300" />
          </InputLeftElement>
          <Input
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            bg={useColorModeValue('white', 'gray.700')}
          />
        </InputGroup>
      </Box>

      {/* Documents Section */}
      <Box flex="1" overflowY="auto">
        <VStack spacing={0} align="stretch">
          {/* Documents Header */}
          <Button
            variant="ghost"
            justifyContent="space-between"
            onClick={onDocumentsToggle}
            px={4}
            py={2}
            borderRadius="none"
            fontWeight="medium"
            fontSize="sm"
          >
            <HStack>
              <Text>Documents ({filteredDocuments.length})</Text>
            </HStack>
            {isDocumentsOpen ? <FiChevronDown /> : <FiChevronRight />}
          </Button>

          {/* Documents List */}
          <Collapse in={isDocumentsOpen}>
            <VStack spacing={0} align="stretch">
              {isLoading ? (
                <Flex justify="center" p={8}>
                  <Spinner size="md" />
                </Flex>
              ) : filteredDocuments.length === 0 ? (
                <Box p={4}>
                  {searchTerm ? (
                    <Alert status="info" size="sm">
                      <AlertIcon />
                      <Box>
                        <AlertTitle fontSize="xs">No matches found</AlertTitle>
                        <AlertDescription fontSize="xs">
                          Try adjusting your search terms.
                        </AlertDescription>
                      </Box>
                    </Alert>
                  ) : (
                    <Alert status="info" size="sm">
                      <AlertIcon />
                      <Box>
                        <AlertTitle fontSize="xs">No documents yet</AlertTitle>
                        <AlertDescription fontSize="xs">
                          Upload documents to this workflow to get started.
                        </AlertDescription>
                      </Box>
                    </Alert>
                  )}
                </Box>
              ) : (
                filteredDocuments.map((document) => (
                  <Box
                    key={document.doc_id || document.id}
                    p={3}
                    bg={selectedDoc?.doc_id === document.doc_id ? selectedBg : 'transparent'}
                    _hover={{ bg: hoverBg }}
                    borderBottom="1px"
                    borderColor={borderColor}
                    cursor="pointer"
                    onClick={() => handleDocumentClick(document)}
                  >
                    <VStack align="stretch" spacing={2}>
                      <Text fontSize="sm" fontWeight="medium" noOfLines={2}>
                        {document.title || `${document.doc_type} Document`}
                      </Text>
                      
                      {document.workflow_doc_type === 'circular' && document.category && (
                        <Badge colorScheme="blue" fontSize="xs" w="fit-content">
                          {document.category}
                        </Badge>
                      )}
                      
                      <Text fontSize="xs" color="gray.500">
                        Added: {formatDate(document.added_at || document.date_published)}
                      </Text>
                      
                      <Flex gap={2} fontSize="xs">
                        {document.workflow_doc_type === 'press_release' ? (
                          <>
                            {document.press_release_link && (
                              <Link 
                                href={document.press_release_link} 
                                isExternal 
                                color="blue.500"
                                display="inline-flex"
                                alignItems="center"
                                gap={1}
                                onClick={(e) => e.stopPropagation()}
                              >
                                View <FiExternalLink />
                              </Link>
                            )}
                            
                            {document.pdf_link && (
                              <Link 
                                href={document.pdf_link} 
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
                          document.pdf_link && (
                            <Link 
                              href={document.pdf_link} 
                              isExternal
                              color="blue.500"
                              display="inline-flex"
                              alignItems="center"
                              gap={1}
                              onClick={(e) => e.stopPropagation()}
                            >
                              View Circular <FiFileText />
                            </Link>
                          )
                        )}
                      </Flex>
                      
                      <Badge size="xs" colorScheme={document.workflow_doc_type === 'press_release' ? 'green' : 'purple'}>
                        {document.workflow_doc_type === 'press_release' ? 'Press Release' : 'Circular'}
                      </Badge>
                    </VStack>
                  </Box>
                ))
              )}
            </VStack>
          </Collapse>
        </VStack>
      </Box>

    </Box>
  )
}

export default WorkflowRightSidebar
