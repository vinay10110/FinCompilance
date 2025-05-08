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
  Divider,
} from '@chakra-ui/react'
import {
  FiClock,
  FiUser,
  FiAlertTriangle,
  FiCheckCircle,
  FiBarChart,
} from 'react-icons/fi'

const ImplementationPlan = () => {
  const { id } = useParams()
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  useEffect(() => {
    fetchPlan()
  }, [id])

  const fetchPlan = async () => {
    try {
      const response = await fetch(`/api/results/${id}`)
      if (!response.ok) {
        throw new Error('Failed to fetch implementation plan')
      }
      const data = await response.json()
      setPlan(data.implementation_plan)
    } catch (error) {
      console.error('Error fetching plan:', error)
      toast({
        title: 'Error',
        description: 'Failed to load implementation plan',
        status: 'error',
        duration: 5000,
        isClosable: true,
      })
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'red',
      medium: 'yellow',
      low: 'green',
    }
    return colors[priority.toLowerCase()] || 'gray'
  }

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" />
        <Text mt={4}>Loading implementation plan...</Text>
      </Box>
    )
  }

  if (!plan) {
    return (
      <Box textAlign="center" py={10}>
        <Icon as={FiAlertTriangle} w={8} h={8} color="red.500" />
        <Text mt={4}>Implementation plan not found</Text>
      </Box>
    )
  }

  return (
    <Box>
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="lg">Implementation Plan</Heading>
          <Text color="gray.600">Document ID: {plan.document_id}</Text>
        </Box>

        <Grid templateColumns="repeat(3, 1fr)" gap={6}>
          <GridItem>
            <Card>
              <CardHeader>
                <HStack>
                  <Icon as={FiBarChart} />
                  <Text fontWeight="bold">Overall Progress</Text>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack align="stretch" spacing={4}>
                  <Progress
                    value={plan.tasks.reduce(
                      (acc, task) => acc + task.progress,
                      0
                    ) / plan.tasks.length}
                    size="lg"
                    colorScheme="blue"
                  />
                  <Text textAlign="center">
                    {Math.round(
                      plan.tasks.reduce(
                        (acc, task) => acc + task.progress,
                        0
                      ) / plan.tasks.length
                    )}
                    % Complete
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          </GridItem>

          <GridItem>
            <Card>
              <CardHeader>
                <HStack>
                  <Icon as={FiClock} />
                  <Text fontWeight="bold">Timeline</Text>
                </HStack>
              </CardHeader>
              <CardBody>
                <VStack align="stretch">
                  <Text>
                    Estimated Hours: {plan.total_estimated_hours}
                  </Text>
                  <Text>
                    Start Date:{' '}
                    {new Date(plan.created_at).toLocaleDateString()}
                  </Text>
                </VStack>
              </CardBody>
            </Card>
          </GridItem>

          <GridItem>
            <Card>
              <CardHeader>
                <HStack>
                  <Icon as={FiAlertTriangle} />
                  <Text fontWeight="bold">Risk Assessment</Text>
                </HStack>
              </CardHeader>
              <CardBody>
                <List spacing={2}>
                  {Object.entries(plan.risk_assessment).map(
                    ([risk, level]) => (
                      <ListItem key={risk}>
                        <Badge
                          colorScheme={getPriorityColor(level)}
                          mr={2}
                        >
                          {level}
                        </Badge>
                        {risk}
                      </ListItem>
                    )
                  )}
                </List>
              </CardBody>
            </Card>
          </GridItem>
        </Grid>

        <Box>
          <Heading size="md" mb={4}>
            Tasks
          </Heading>
          <VStack spacing={4} align="stretch">
            {plan.tasks.map((task) => (
              <Card key={task.id}>
                <CardBody>
                  <Grid templateColumns="1fr auto" gap={4}>
                    <VStack align="stretch" spacing={2}>
                      <HStack>
                        <Text fontWeight="bold">{task.title}</Text>
                        <Badge
                          colorScheme={getPriorityColor(task.priority)}
                        >
                          {task.priority}
                        </Badge>
                      </HStack>
                      <Text color="gray.600">{task.description}</Text>
                      <Progress
                        value={task.progress}
                        size="sm"
                        colorScheme="blue"
                      />
                      <HStack spacing={4} fontSize="sm" color="gray.600">
                        <HStack>
                          <Icon as={FiUser} />
                          <Text>
                            {task.assigned_to || 'Unassigned'}
                          </Text>
                        </HStack>
                        <HStack>
                          <Icon as={FiClock} />
                          <Text>{task.estimated_hours}h</Text>
                        </HStack>
                      </HStack>
                    </VStack>

                    <VStack>
                      <Button
                        size="sm"
                        colorScheme={
                          task.status === 'completed'
                            ? 'green'
                            : 'blue'
                        }
                        leftIcon={
                          <Icon
                            as={
                              task.status === 'completed'
                                ? FiCheckCircle
                                : undefined
                            }
                          />
                        }
                      >
                        {task.status === 'completed'
                          ? 'Completed'
                          : 'Mark Complete'}
                      </Button>
                    </VStack>
                  </Grid>
                </CardBody>
              </Card>
            ))}
          </VStack>
        </Box>

        <Divider />

        <Box>
          <Heading size="md" mb={4}>
            Resource Allocation
          </Heading>
          <Grid templateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={4}>
            {Object.entries(plan.resources).map(([role, resources]) => (
              <Card key={role}>
                <CardHeader>
                  <Text fontWeight="bold">{role}</Text>
                </CardHeader>
                <CardBody>
                  <List spacing={2}>
                    {resources.map((resource, index) => (
                      <ListItem key={index}>
                        <HStack>
                          <Icon as={FiUser} />
                          <Text>{resource}</Text>
                        </HStack>
                      </ListItem>
                    ))}
                  </List>
                </CardBody>
              </Card>
            ))}
          </Grid>
        </Box>
      </VStack>
    </Box>
  )
}

export default ImplementationPlan