import { useState, useEffect } from 'react'
import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Spinner,
  useToast,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Icon,
} from '@chakra-ui/react'
import { Link as RouterLink } from 'react-router-dom'
import { FiFileText, FiCheckCircle, FiAlertTriangle } from 'react-icons/fi'

const ResultsList = () => {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    fetchResults()
  }, [])

  const fetchResults = async () => {
    try {
      const response = await fetch('/api/results')
      if (!response.ok) {
        throw new Error('Failed to fetch results')
      }
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error fetching results:', error)
      toast({
        title: 'Error',
        description: 'Failed to load analysis results',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusProps = {
      compliance_verification_complete: {
        colorScheme: 'green',
        text: 'Verified',
        icon: FiCheckCircle,
      },
      implementation_plan_complete: {
        colorScheme: 'blue',
        text: 'Plan Ready',
        icon: FiFileText,
      },
      change_analysis_complete: {
        colorScheme: 'yellow',
        text: 'Analysis Complete',
        icon: FiFileText,
      },
      error: {
        colorScheme: 'red',
        text: 'Error',
        icon: FiAlertTriangle,
      },
    }[status] || {
      colorScheme: 'gray',
      text: status,
      icon: FiFileText,
    }

    return (
      <Badge
        colorScheme={statusProps.colorScheme}
        display="flex"
        alignItems="center"
        gap={1}
      >
        <Icon as={statusProps.icon} />
        {statusProps.text}
      </Badge>
    )
  }

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" />
        <Text mt={4}>Loading results...</Text>
      </Box>
    )
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
          Analysis Results
        </Text>

        {results.length === 0 ? (
          <Text color="gray.600" textAlign="center" py={4}>
            No analysis results available
          </Text>
        ) : (
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Date</Th>
                <Th>Status</Th>
                <Th>Implementation Plan</Th>
                <Th>Compliance Status</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {results.map((result) => (
                <Tr key={result.id}>
                  <Td>{new Date(result.timestamp).toLocaleDateString()}</Td>
                  <Td>{getStatusBadge(result.status)}</Td>
                  <Td>
                    {result.has_implementation_plan ? (
                      <Badge colorScheme="green">Available</Badge>
                    ) : (
                      <Badge colorScheme="gray">Not Available</Badge>
                    )}
                  </Td>
                  <Td>
                    {result.has_compliance_status ? (
                      <Badge colorScheme="green">Verified</Badge>
                    ) : (
                      <Badge colorScheme="gray">Pending</Badge>
                    )}
                  </Td>
                  <Td>
                    <HStack spacing={2}>
                      {result.has_implementation_plan && (
                        <Button
                          as={RouterLink}
                          to={`/plan/${result.id}`}
                          size="sm"
                          colorScheme="blue"
                          variant="outline"
                        >
                          View Plan
                        </Button>
                      )}
                      {result.has_compliance_status && (
                        <Button
                          as={RouterLink}
                          to={`/verify/${result.id}`}
                          size="sm"
                          colorScheme="green"
                          variant="outline"
                        >
                          View Compliance
                        </Button>
                      )}
                    </HStack>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </VStack>
    </Box>
  )
}

export default ResultsList