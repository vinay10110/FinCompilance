import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Spinner,
  useToast,
  Grid,
  GridItem,
  Progress,
  Badge,
  Card,
  CardHeader,
  CardBody,
  List,
  ListItem,
  Icon,
  Button,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react'
import {
  FiCheck,
  FiX,
  FiAlertTriangle,
  FiFileText,
  FiCheckCircle,
} from 'react-icons/fi'

const ComplianceVerification = () => {
  const { id } = useParams()
  const [verification, setVerification] = useState(null)
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    fetchVerification()
  }, [id])

  const fetchVerification = async () => {
    try {
      const response = await fetch(`/api/results/${id}`)
      if (!response.ok) {
        throw new Error('Failed to fetch compliance verification')
      }
      const data = await response.json()
      setVerification(data.compliance_status)
    } catch (error) {
      console.error('Error fetching verification:', error)
      toast({
        title: 'Error',
        description: 'Failed to load compliance verification',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'compliant':
        return <Icon as={FiCheck} color="green.500" />
      case 'non_compliant':
        return <Icon as={FiX} color="red.500" />
      case 'partial':
        return <Icon as={FiAlertTriangle} color="yellow.500" />
      default:
        return null
    }
  }

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" />
        <Text mt={4}>Loading compliance verification...</Text>
      </Box>
    )
  }

  if (!verification) {
    return (
      <Box textAlign="center" py={10}>
        <Icon as={FiAlertTriangle} w={8} h={8} color="red.500" />
        <Text mt={4}>Compliance verification not found</Text>
      </Box>
    )
  }

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg">Compliance Verification</Heading>
          <Text color="gray.600">
            Plan ID: {verification.plan_id}
          </Text>
        </Box>

        <Grid templateColumns="repeat(3, 1fr)" gap={6}>
          <GridItem>
            <Card>
              <CardHeader>
                <HStack>
                  <Icon as={FiCheckCircle} />
                  <Text fontWeight="bold">Compliance Score</Text>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack align="stretch" spacing={4}>
                  <Progress
                    value={verification.compliance_score}
                    size="lg"
                    colorScheme={
                      verification.compliance_score >= 90
                        ? 'green'
                        : verification.compliance_score >= 70
                        ? 'yellow'
                        : 'red'
                    }
                  />
                  <Text textAlign="center" fontSize="xl" fontWeight="bold">
                    {verification.compliance_score}%
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          </GridItem>

          <GridItem>
            <Card>
              <CardHeader>
                <HStack>
                  <Icon as={FiFileText} />
                  <Text fontWeight="bold">Verification Summary</Text>
                </HStack>
              </CardHeader>
              <CardBody>
                <List spacing={2}>
                  <ListItem>
                    <HStack justify="space-between">
                      <Text>Status</Text>
                      <Badge
                        colorScheme={
                          verification.status === 'completed'
                            ? 'green'
                            : 'yellow'
                        }
                      >
                        {verification.status}
                      </Badge>
                    </HStack>
                  </ListItem>
                  <ListItem>
                    <HStack justify="space-between">
                      <Text>Verified By</Text>
                      <Text>{verification.reviewer || 'Auto-verified'}</Text>
                    </HStack>
                  </ListItem>
                  <ListItem>
                    <HStack justify="space-between">
                      <Text>Verification Date</Text>
                      <Text>
                        {new Date(
                          verification.verification_date
                        ).toLocaleDateString()}
                      </Text>
                    </HStack>
                  </ListItem>
                </List>
              </CardBody>
            </Card>
          </GridItem>

          <GridItem>
            <Card>
              <CardHeader>
                <HStack>
                  <Icon as={FiAlertTriangle} />
                  <Text fontWeight="bold">Issues Summary</Text>
                </HStack>
              </CardHeader>
              <CardBody>
                <List spacing={2}>
                  <ListItem>
                    <HStack justify="space-between">
                      <Text>Critical Issues</Text>
                      <Badge colorScheme="red">
                        {verification.issues.filter(
                          (issue) => issue.severity === 'critical'
                        ).length}
                      </Badge>
                    </HStack>
                  </ListItem>
                  <ListItem>
                    <HStack justify="space-between">
                      <Text>Major Issues</Text>
                      <Badge colorScheme="orange">
                        {verification.issues.filter(
                          (issue) => issue.severity === 'major'
                        ).length}
                      </Badge>
                    </HStack>
                  </ListItem>
                  <ListItem>
                    <HStack justify="space-between">
                      <Text>Minor Issues</Text>
                      <Badge colorScheme="yellow">
                        {verification.issues.filter(
                          (issue) => issue.severity === 'minor'
                        ).length}
                      </Badge>
                    </HStack>
                  </ListItem>
                </List>
              </CardBody>
            </Card>
          </GridItem>
        </Grid>

        <Box>
          <Heading size="md" mb={4}>
            Requirements Compliance
          </Heading>
          <Accordion allowMultiple>
            {Object.entries(verification.requirements_status).map(
              ([reqId, status]) => (
                <AccordionItem key={reqId}>
                  <AccordionButton>
                    <Box flex="1">
                      <HStack>
                        {getStatusIcon(status.status)}
                        <Text fontWeight="bold">
                          Requirement {reqId}
                        </Text>
                        <Badge
                          colorScheme={
                            status.status === 'compliant'
                              ? 'green'
                              : status.status === 'non_compliant'
                              ? 'red'
                              : 'yellow'
                          }
                        >
                          {status.status}
                        </Badge>
                      </HStack>
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel>
                    <VStack align="stretch" spacing={4}>
                      <Text>{status.description}</Text>
                      {status.findings.length > 0 && (
                        <Box>
                          <Text fontWeight="bold">Findings:</Text>
                          <List spacing={2}>
                            {status.findings.map((finding, idx) => (
                              <ListItem key={idx}>
                                <HStack>
                                  <Icon
                                    as={
                                      finding.type === 'success'
                                        ? FiCheck
                                        : FiAlertTriangle
                                    }
                                    color={
                                      finding.type === 'success'
                                        ? 'green.500'
                                        : 'yellow.500'
                                    }
                                  />
                                  <Text>{finding.description}</Text>
                                </HStack>
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                      {status.evidence && (
                        <Box>
                          <Text fontWeight="bold">Evidence:</Text>
                          <Text>{status.evidence}</Text>
                        </Box>
                      )}
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              )
            )}
          </Accordion>
        </Box>

        {verification.issues.length > 0 && (
          <Box>
            <Heading size="md" mb={4}>
              Issues Requiring Attention
            </Heading>
            <VStack spacing={4} align="stretch">
              {verification.issues.map((issue, idx) => (
                <Card key={idx}>
                  <CardBody>
                    <HStack spacing={4}>
                      <Icon
                        as={FiAlertTriangle}
                        color={
                          issue.severity === 'critical'
                            ? 'red.500'
                            : issue.severity === 'major'
                            ? 'orange.500'
                            : 'yellow.500'
                        }
                        w={6}
                        h={6}
                      />
                      <VStack align="stretch" flex={1}>
                        <HStack justify="space-between">
                          <Text fontWeight="bold">
                            {issue.title}
                          </Text>
                          <Badge
                            colorScheme={
                              issue.severity === 'critical'
                                ? 'red'
                                : issue.severity === 'major'
                                ? 'orange'
                                : 'yellow'
                            }
                          >
                            {issue.severity}
                          </Badge>
                        </HStack>
                        <Text color="gray.600">
                          {issue.description}
                        </Text>
                        {issue.recommendation && (
                          <Text color="blue.600">
                            Recommendation: {issue.recommendation}
                          </Text>
                        )}
                      </VStack>
                    </HStack>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          </Box>
        )}
      </VStack>
    </Box>
  )
}

export default ComplianceVerification