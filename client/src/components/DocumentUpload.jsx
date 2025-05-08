import { useState } from 'react'
import {
  Box,
  Button,
  VStack,
  useToast,
  Progress,
  Text,
  Icon,
  Input,
  FormControl,
  FormLabel,
} from '@chakra-ui/react'
import { FiUpload } from 'react-icons/fi'

const DocumentUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const toast = useToast()

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file)
    } else {
      toast({
        title: 'Invalid file type',
        description: 'Please select a PDF file',
        status: 'error',
        duration: 3000,
        isClosable: true,
      })
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      toast({
        title: 'No file selected',
        description: 'Please select a PDF file to upload',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      })
      return
    }

    try {
      setUploading(true)
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Simulated progress updates
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90))
      }, 500)

      const response = await fetch('/api/process-document', {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressInterval)

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()
      setProgress(100)

      toast({
        title: 'Upload successful',
        description: 'Document has been processed successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      })

      // Reset form after successful upload
      setTimeout(() => {
        setProgress(0)
        setSelectedFile(null)
        setUploading(false)
      }, 1000)

    } catch (error) {
      console.error('Upload error:', error)
      toast({
        title: 'Upload failed',
        description: error.message || 'An error occurred during upload',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
      setProgress(0)
      setUploading(false)
    }
  }

  return (
    <Box
      borderWidth="1px"
      borderRadius="lg"
      p={6}
      bg="white"
      shadow="sm"
    >
      <VStack spacing={4} align="stretch">
        <Text fontSize="xl" fontWeight="bold">
          Upload Regulatory Document
        </Text>

        <FormControl>
          <FormLabel>Select PDF Document</FormLabel>
          <Input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            disabled={uploading}
          />
        </FormControl>

        {selectedFile && (
          <Text fontSize="sm" color="gray.600">
            Selected file: {selectedFile.name}
          </Text>
        )}

        {progress > 0 && (
          <Progress
            value={progress}
            size="sm"
            colorScheme="blue"
            borderRadius="full"
          />
        )}

        <Button
          leftIcon={<Icon as={FiUpload} />}
          colorScheme="blue"
          onClick={handleUpload}
          isLoading={uploading}
          loadingText="Processing..."
          disabled={!selectedFile || uploading}
        >
          Upload and Process
        </Button>
      </VStack>
    </Box>
  )
}

export default DocumentUpload