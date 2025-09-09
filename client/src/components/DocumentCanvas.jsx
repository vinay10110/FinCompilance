import { useState } from 'react'
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
  Box,
  useColorModeValue,
  IconButton,
  Tooltip,
  Divider,
  Badge,
  Textarea
} from '@chakra-ui/react'
import { FiDownload, FiFileText, FiEdit3, FiSave } from 'react-icons/fi'

const DocumentCanvas = ({ 
  isOpen, 
  onClose, 
  document, 
  title = "Generated Document" 
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editedContent, setEditedContent] = useState('')

  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.600')
  const codeBg = useColorModeValue('gray.50', 'gray.700')

  // Extract content from document for display
  const getDocumentContent = () => {
    if (!document) return ''
    
    // If document has content_base64, it's a generated document
    if (document.content_base64) {
      try {
        // For display purposes, we'll show a preview message
        return `Document "${document.filename}" has been generated and is ready for download.`
      } catch (error) {
        return 'Document content could not be displayed.'
      }
    }
    
    // If document has text content directly
    if (document.content) {
      return document.content
    }
    
    return 'No document content available.'
  }

  const handleDownloadWord = () => {
    if (!document?.content_base64) return
    
    try {
      // Convert base64 to blob and download
      const byteCharacters = atob(document.content_base64)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { 
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
      })
      
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = document.filename || 'compliance_report.docx'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Error downloading document:', error)
    }
  }

  const handleDownloadPDF = () => {
    // For now, we'll show an alert. PDF conversion would need additional backend support
    alert('PDF download will be available in a future update. Please use Word download for now.')
  }

  const handleEdit = () => {
    setEditedContent(getDocumentContent())
    setIsEditing(true)
  }

  const handleSaveEdit = () => {
    // For now, just close edit mode. In future, could send back to agent for regeneration
    setIsEditing(false)
    alert('Document editing will be fully implemented in a future update.')
  }

  if (!document) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl" scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent bg={bgColor} maxH="90vh">
        <ModalHeader>
          <HStack justify="space-between" align="center">
            <HStack>
              <FiFileText />
              <Text>{title}</Text>
              <Badge colorScheme="blue" size="sm">
                {document.filename ? 'Generated' : 'Preview'}
              </Badge>
            </HStack>
            <HStack spacing={2}>
              <Tooltip label="Edit document">
                <IconButton
                  icon={<FiEdit3 />}
                  size="sm"
                  variant="ghost"
                  onClick={handleEdit}
                  isDisabled={!document.content_base64}
                />
              </Tooltip>
            </HStack>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <VStack spacing={4} align="stretch">
            {document.filename && (
              <Box p={3} bg={codeBg} borderRadius="md" border="1px" borderColor={borderColor}>
                <Text fontSize="sm" color="gray.600">
                  <strong>Filename:</strong> {document.filename}
                </Text>
              </Box>
            )}
            
            <Divider />
            
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={2}>
                Document Content:
              </Text>
              
              {isEditing ? (
                <VStack spacing={3} align="stretch">
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    minH="300px"
                    placeholder="Edit document content..."
                    bg={useColorModeValue('white', 'gray.700')}
                  />
                  <HStack justify="flex-end">
                    <Button size="sm" onClick={() => setIsEditing(false)}>
                      Cancel
                    </Button>
                    <Button 
                      size="sm" 
                      colorScheme="blue" 
                      leftIcon={<FiSave />}
                      onClick={handleSaveEdit}
                    >
                      Save Changes
                    </Button>
                  </HStack>
                </VStack>
              ) : (
                <Box
                  p={4}
                  bg={codeBg}
                  borderRadius="md"
                  border="1px"
                  borderColor={borderColor}
                  minH="300px"
                  maxH="400px"
                  overflowY="auto"
                >
                  <Text fontSize="sm" whiteSpace="pre-wrap">
                    {getDocumentContent()}
                  </Text>
                </Box>
              )}
            </Box>
          </VStack>
        </ModalBody>

        <ModalFooter>
          <HStack spacing={3}>
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
            
            {document.content_base64 && (
              <>
                <Button
                  leftIcon={<FiDownload />}
                  colorScheme="green"
                  onClick={handleDownloadWord}
                >
                  Download Word
                </Button>
                
                <Button
                  leftIcon={<FiDownload />}
                  colorScheme="red"
                  onClick={handleDownloadPDF}
                  isDisabled
                >
                  Download PDF
                </Button>
              </>
            )}
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}

export default DocumentCanvas
