import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Dimensions,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/contexts/AuthContext';
import api from '../../src/services/api';
import sultanFeedback from '../../src/utils/sultanFeedback';

const { width } = Dimensions.get('window');

interface Course {
  course_id: string;
  title: string;
  description: string;
  category: string;
  difficulty: string;
  duration_hours: number;
  lessons_count: number;
  price: number;
  rating: number;
  enrollments: number;
  instructor: string;
  rewards: {
    completion_coins: number;
    per_lesson_coins: number;
  };
}

interface MindGame {
  game_id: string;
  name: string;
  description: string;
  category: string;
  difficulty: string;
  coins_reward: number;
  time_limit_seconds: number;
}

interface EducationProfile {
  total_learning_hours: number;
  current_level: string;
  total_coins_earned: number;
  courses_enrolled: number;
  courses_completed: number;
  games_played: number;
  streak_days: number;
}

interface LearningLevel {
  min_hours: number;
  reward: number;
  badge_color: string;
}

export default function EducationScreen() {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [mindGames, setMindGames] = useState<MindGame[]>([]);
  const [profile, setProfile] = useState<EducationProfile | null>(null);
  const [learningLevels, setLearningLevels] = useState<Record<string, LearningLevel>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'courses' | 'games'>('courses');
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null);
  const [selectedGame, setSelectedGame] = useState<MindGame | null>(null);
  const [enrolling, setEnrolling] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [gameResult, setGameResult] = useState<{ won: boolean; coins: number } | null>(null);

  const fetchData = async () => {
    try {
      const [configRes, coursesRes, gamesRes, profileRes] = await Promise.all([
        api.get('/education/config'),
        api.get('/education/courses'),
        api.get('/education/mind-games'),
        api.get('/education/profile').catch(() => ({ data: null })),
      ]);

      setLearningLevels(configRes.data.learning_levels);
      setCourses(coursesRes.data.courses);
      setMindGames(gamesRes.data.games);
      if (profileRes.data) {
        setProfile(profileRes.data);
      }
    } catch (error) {
      console.error('Error fetching education data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, []);

  const handleEnroll = async (course: Course) => {
    setEnrolling(true);
    try {
      await api.post('/education/enroll', { course_id: course.course_id });
      await sultanFeedback.taskComplete(); // Royal sound + vibration
      await fetchData();
      setSelectedCourse(null);
      alert(`🎉 Successfully enrolled in ${course.title}!`);
    } catch (error: any) {
      await sultanFeedback.error();
      alert(error.response?.data?.detail || 'Failed to enroll');
    } finally {
      setEnrolling(false);
    }
  };

  const handlePlayGame = async (game: MindGame) => {
    setPlaying(true);
    await sultanFeedback.buttonPress(); // Click feedback
    try {
      // Simulate game play with random score
      const score = Math.floor(Math.random() * 100);
      const response = await api.post('/education/play-mind-game', {
        game_id: game.game_id,
        score: score,
        time_taken: Math.floor(Math.random() * game.time_limit_seconds),
      });
      
      if (response.data.won) {
        await sultanFeedback.gameWon(); // Victory sound + vibration
      } else {
        await sultanFeedback.gameLost(); // Lose feedback
      }
      
      setGameResult({
        won: response.data.won,
        coins: response.data.coins_earned,
      });
    } catch (error: any) {
      await sultanFeedback.error();
      alert(error.response?.data?.detail || 'Failed to play game');
    } finally {
      setPlaying(false);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return '#4CAF50';
      case 'medium':
        return '#FF9800';
      case 'hard':
        return '#F44336';
      case 'beginner':
        return '#4CAF50';
      case 'intermediate':
        return '#FF9800';
      case 'advanced':
        return '#F44336';
      default:
        return '#2196F3';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'mathematics':
        return 'calculator';
      case 'science':
        return 'flask';
      case 'english':
        return 'book';
      case 'computer science':
        return 'laptop';
      case 'business':
        return 'briefcase';
      case 'arts':
        return 'color-palette';
      case 'languages':
        return 'language';
      case 'life skills':
        return 'heart';
      case 'mind games':
        return 'game-controller';
      default:
        return 'school';
    }
  };

  const getLevelBadge = (level: string) => {
    const levelData = learningLevels[level];
    return levelData?.badge_color || '#4CAF50';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <LinearGradient colors={['#1A1A2E', '#16213E', '#0F3460']} style={styles.gradient}>
          <ActivityIndicator size="large" color="#FFD700" />
          <Text style={styles.loadingText}>Loading Education Platform...</Text>
        </LinearGradient>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <LinearGradient colors={['#1A1A2E', '#16213E', '#0F3460']} style={styles.gradient}>
        <SafeAreaView style={styles.safeArea}>
          <ScrollView
            style={styles.scrollView}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFD700" />
            }
            showsVerticalScrollIndicator={false}
          >
            {/* Header */}
            <View style={styles.header}>
              <View>
                <Text style={styles.headerTitle}>📚 Education</Text>
                <Text style={styles.headerSubtitle}>Learn & Earn Rewards</Text>
              </View>
              <View style={styles.streakBadge}>
                <Ionicons name="flame" size={20} color="#FF6B35" />
                <Text style={styles.streakText}>{profile?.streak_days || 0}</Text>
              </View>
            </View>

            {/* Profile Stats Card */}
            <LinearGradient
              colors={['#2A2A4E', '#1A1A3E']}
              style={styles.profileCard}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <View style={styles.profileHeader}>
                <View style={[styles.levelBadge, { backgroundColor: getLevelBadge(profile?.current_level || 'seedling') }]}>
                  <Text style={styles.levelEmoji}>🌱</Text>
                </View>
                <View style={styles.profileInfo}>
                  <Text style={styles.levelName}>
                    {(profile?.current_level || 'Seedling').replace('_', ' ').toUpperCase()}
                  </Text>
                  <Text style={styles.learningHours}>
                    {profile?.total_learning_hours || 0} hours learned
                  </Text>
                </View>
              </View>
              
              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{profile?.courses_enrolled || 0}</Text>
                  <Text style={styles.statLabel}>Enrolled</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{profile?.courses_completed || 0}</Text>
                  <Text style={styles.statLabel}>Completed</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{profile?.games_played || 0}</Text>
                  <Text style={styles.statLabel}>Games</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, { color: '#FFD700' }]}>
                    {profile?.total_coins_earned || 0}
                  </Text>
                  <Text style={styles.statLabel}>Earned</Text>
                </View>
              </View>
            </LinearGradient>

            {/* Tab Selector */}
            <View style={styles.tabContainer}>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'courses' && styles.activeTab]}
                onPress={() => setSelectedTab('courses')}
              >
                <Ionicons
                  name="book"
                  size={20}
                  color={selectedTab === 'courses' ? '#FFD700' : '#808080'}
                />
                <Text style={[styles.tabText, selectedTab === 'courses' && styles.activeTabText]}>
                  Courses
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.tab, selectedTab === 'games' && styles.activeTab]}
                onPress={() => setSelectedTab('games')}
              >
                <Ionicons
                  name="flash"
                  size={20}
                  color={selectedTab === 'games' ? '#FFD700' : '#808080'}
                />
                <Text style={[styles.tabText, selectedTab === 'games' && styles.activeTabText]}>
                  Gyan Yuddh
                </Text>
              </TouchableOpacity>
            </View>

            {/* Courses Tab */}
            {selectedTab === 'courses' && (
              <View style={styles.contentSection}>
                <Text style={styles.sectionTitle}>📖 Available Courses</Text>
                {courses.map((course) => (
                  <TouchableOpacity
                    key={course.course_id}
                    style={styles.courseCard}
                    onPress={() => setSelectedCourse(course)}
                  >
                    <LinearGradient
                      colors={['rgba(255,255,255,0.08)', 'rgba(255,255,255,0.02)']}
                      style={styles.courseGradient}
                    >
                      <View style={styles.courseHeader}>
                        <View style={[styles.categoryIcon, { backgroundColor: getDifficultyColor(course.difficulty) + '30' }]}>
                          <Ionicons
                            name={getCategoryIcon(course.category) as any}
                            size={24}
                            color={getDifficultyColor(course.difficulty)}
                          />
                        </View>
                        <View style={styles.courseInfo}>
                          <Text style={styles.courseTitle}>{course.title}</Text>
                          <Text style={styles.courseInstructor}>by {course.instructor}</Text>
                        </View>
                        <View style={[styles.difficultyBadge, { backgroundColor: getDifficultyColor(course.difficulty) + '30' }]}>
                          <Text style={[styles.difficultyText, { color: getDifficultyColor(course.difficulty) }]}>
                            {course.difficulty}
                          </Text>
                        </View>
                      </View>
                      
                      <Text style={styles.courseDescription} numberOfLines={2}>
                        {course.description}
                      </Text>
                      
                      <View style={styles.courseFooter}>
                        <View style={styles.courseStats}>
                          <View style={styles.courseStat}>
                            <Ionicons name="time" size={14} color="#808080" />
                            <Text style={styles.courseStatText}>{course.duration_hours}h</Text>
                          </View>
                          <View style={styles.courseStat}>
                            <Ionicons name="list" size={14} color="#808080" />
                            <Text style={styles.courseStatText}>{course.lessons_count} lessons</Text>
                          </View>
                          <View style={styles.courseStat}>
                            <Ionicons name="people" size={14} color="#808080" />
                            <Text style={styles.courseStatText}>{course.enrollments}</Text>
                          </View>
                        </View>
                        <View style={styles.courseReward}>
                          <Ionicons name="trophy" size={14} color="#FFD700" />
                          <Text style={styles.rewardText}>{course.rewards.completion_coins} coins</Text>
                        </View>
                      </View>
                      
                      <View style={styles.ratingContainer}>
                        {[1, 2, 3, 4, 5].map((star) => (
                          <Ionicons
                            key={star}
                            name={star <= Math.floor(course.rating) ? 'star' : 'star-outline'}
                            size={14}
                            color="#FFD700"
                          />
                        ))}
                        <Text style={styles.ratingText}>{course.rating}</Text>
                      </View>
                    </LinearGradient>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* Gyan Yuddh Tab */}
            {selectedTab === 'games' && (
              <View style={styles.contentSection}>
                <Text style={styles.sectionTitle}>⚔️ Gyan Yuddh (ज्ञान युद्ध)</Text>
                <Text style={styles.sectionSubtitle}>Knowledge Battle - Train your brain and earn rewards!</Text>
                
                <View style={styles.gamesGrid}>
                  {mindGames.map((game) => (
                    <TouchableOpacity
                      key={game.game_id}
                      style={styles.gameCard}
                      onPress={() => setSelectedGame(game)}
                    >
                      <LinearGradient
                        colors={[getDifficultyColor(game.difficulty) + '40', getDifficultyColor(game.difficulty) + '10']}
                        style={styles.gameGradient}
                      >
                        <View style={styles.gameIcon}>
                          <Ionicons name="game-controller" size={32} color={getDifficultyColor(game.difficulty)} />
                        </View>
                        <Text style={styles.gameName}>{game.name}</Text>
                        <Text style={styles.gameDescription} numberOfLines={2}>
                          {game.description}
                        </Text>
                        <View style={styles.gameFooter}>
                          <View style={[styles.gameDifficulty, { backgroundColor: getDifficultyColor(game.difficulty) + '30' }]}>
                            <Text style={[styles.gameDifficultyText, { color: getDifficultyColor(game.difficulty) }]}>
                              {game.difficulty}
                            </Text>
                          </View>
                          <View style={styles.gameReward}>
                            <Ionicons name="logo-bitcoin" size={14} color="#FFD700" />
                            <Text style={styles.gameRewardText}>{game.coins_reward}</Text>
                          </View>
                        </View>
                        <View style={styles.gameTime}>
                          <Ionicons name="timer" size={12} color="#808080" />
                          <Text style={styles.gameTimeText}>{game.time_limit_seconds}s</Text>
                        </View>
                      </LinearGradient>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}

            <View style={{ height: 100 }} />
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>

      {/* Course Detail Modal */}
      <Modal visible={selectedCourse !== null} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <LinearGradient colors={['#2A2A4E', '#1A1A3E']} style={styles.modalGradient}>
              <TouchableOpacity style={styles.closeButton} onPress={() => setSelectedCourse(null)}>
                <Ionicons name="close" size={24} color="#FFFFFF" />
              </TouchableOpacity>
              
              {selectedCourse && (
                <>
                  <View style={styles.modalHeader}>
                    <View style={[styles.modalIcon, { backgroundColor: getDifficultyColor(selectedCourse.difficulty) + '30' }]}>
                      <Ionicons
                        name={getCategoryIcon(selectedCourse.category) as any}
                        size={40}
                        color={getDifficultyColor(selectedCourse.difficulty)}
                      />
                    </View>
                    <Text style={styles.modalTitle}>{selectedCourse.title}</Text>
                    <Text style={styles.modalInstructor}>by {selectedCourse.instructor}</Text>
                  </View>
                  
                  <Text style={styles.modalDescription}>{selectedCourse.description}</Text>
                  
                  <View style={styles.modalStats}>
                    <View style={styles.modalStat}>
                      <Ionicons name="time" size={20} color="#FFD700" />
                      <Text style={styles.modalStatValue}>{selectedCourse.duration_hours}h</Text>
                      <Text style={styles.modalStatLabel}>Duration</Text>
                    </View>
                    <View style={styles.modalStat}>
                      <Ionicons name="list" size={20} color="#4CAF50" />
                      <Text style={styles.modalStatValue}>{selectedCourse.lessons_count}</Text>
                      <Text style={styles.modalStatLabel}>Lessons</Text>
                    </View>
                    <View style={styles.modalStat}>
                      <Ionicons name="trophy" size={20} color="#FF9800" />
                      <Text style={styles.modalStatValue}>{selectedCourse.rewards.completion_coins}</Text>
                      <Text style={styles.modalStatLabel}>Reward</Text>
                    </View>
                  </View>
                  
                  <View style={styles.rewardInfo}>
                    <Ionicons name="gift" size={16} color="#FFD700" />
                    <Text style={styles.rewardInfoText}>
                      Earn {selectedCourse.rewards.per_lesson_coins} coins per lesson
                    </Text>
                  </View>
                  
                  <TouchableOpacity
                    style={styles.enrollButton}
                    onPress={() => handleEnroll(selectedCourse)}
                    disabled={enrolling}
                  >
                    <LinearGradient
                      colors={['#FFD700', '#FFA500']}
                      style={styles.enrollGradient}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                    >
                      {enrolling ? (
                        <ActivityIndicator color="#1A1A2E" />
                      ) : (
                        <>
                          <Ionicons name="school" size={20} color="#1A1A2E" />
                          <Text style={styles.enrollButtonText}>
                            {selectedCourse.price > 0 ? `Enroll for ${selectedCourse.price} coins` : 'Enroll Free'}
                          </Text>
                        </>
                      )}
                    </LinearGradient>
                  </TouchableOpacity>
                </>
              )}
            </LinearGradient>
          </View>
        </View>
      </Modal>

      {/* Game Modal */}
      <Modal visible={selectedGame !== null} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <LinearGradient colors={['#2A2A4E', '#1A1A3E']} style={styles.modalGradient}>
              <TouchableOpacity
                style={styles.closeButton}
                onPress={() => {
                  setSelectedGame(null);
                  setGameResult(null);
                }}
              >
                <Ionicons name="close" size={24} color="#FFFFFF" />
              </TouchableOpacity>
              
              {selectedGame && !gameResult && (
                <>
                  <View style={styles.gameModalHeader}>
                    <View style={[styles.gameModalIcon, { backgroundColor: getDifficultyColor(selectedGame.difficulty) + '30' }]}>
                      <Ionicons name="game-controller" size={50} color={getDifficultyColor(selectedGame.difficulty)} />
                    </View>
                    <Text style={styles.modalTitle}>{selectedGame.name}</Text>
                  </View>
                  
                  <Text style={styles.modalDescription}>{selectedGame.description}</Text>
                  
                  <View style={styles.gameInfo}>
                    <View style={styles.gameInfoItem}>
                      <Ionicons name="timer" size={24} color="#2196F3" />
                      <Text style={styles.gameInfoValue}>{selectedGame.time_limit_seconds}s</Text>
                      <Text style={styles.gameInfoLabel}>Time Limit</Text>
                    </View>
                    <View style={styles.gameInfoItem}>
                      <Ionicons name="trophy" size={24} color="#FFD700" />
                      <Text style={styles.gameInfoValue}>{selectedGame.coins_reward}</Text>
                      <Text style={styles.gameInfoLabel}>Reward</Text>
                    </View>
                  </View>
                  
                  <TouchableOpacity
                    style={styles.playButton}
                    onPress={() => handlePlayGame(selectedGame)}
                    disabled={playing}
                  >
                    <LinearGradient
                      colors={[getDifficultyColor(selectedGame.difficulty), getDifficultyColor(selectedGame.difficulty) + 'CC']}
                      style={styles.playGradient}
                    >
                      {playing ? (
                        <ActivityIndicator color="#FFFFFF" />
                      ) : (
                        <>
                          <Ionicons name="play" size={24} color="#FFFFFF" />
                          <Text style={styles.playButtonText}>Play Now</Text>
                        </>
                      )}
                    </LinearGradient>
                  </TouchableOpacity>
                </>
              )}
              
              {gameResult && (
                <View style={styles.resultContainer}>
                  <View style={[styles.resultIcon, { backgroundColor: gameResult.won ? '#4CAF5030' : '#F4433630' }]}>
                    <Ionicons
                      name={gameResult.won ? 'trophy' : 'sad'}
                      size={60}
                      color={gameResult.won ? '#4CAF50' : '#F44336'}
                    />
                  </View>
                  <Text style={styles.resultTitle}>
                    {gameResult.won ? '🎉 Congratulations!' : '😔 Better Luck Next Time!'}
                  </Text>
                  <Text style={styles.resultCoins}>
                    {gameResult.won ? `+${gameResult.coins} Coins Earned!` : 'No coins earned'}
                  </Text>
                  <TouchableOpacity
                    style={styles.playAgainButton}
                    onPress={() => {
                      setGameResult(null);
                      if (selectedGame) handlePlayGame(selectedGame);
                    }}
                  >
                    <Text style={styles.playAgainText}>Play Again</Text>
                  </TouchableOpacity>
                </View>
              )}
            </LinearGradient>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0A0A0F',
  },
  loadingContainer: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
  },
  loadingText: {
    color: '#FFFFFF',
    marginTop: 16,
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#808080',
    marginTop: 4,
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 107, 53, 0.2)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  streakText: {
    color: '#FF6B35',
    fontWeight: 'bold',
    marginLeft: 4,
    fontSize: 16,
  },
  profileCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  levelBadge: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  levelEmoji: {
    fontSize: 24,
  },
  profileInfo: {
    flex: 1,
  },
  levelName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  learningHours: {
    fontSize: 14,
    color: '#808080',
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderRadius: 12,
    padding: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  statLabel: {
    fontSize: 11,
    color: '#808080',
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 12,
    padding: 4,
    marginBottom: 20,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 10,
  },
  activeTab: {
    backgroundColor: 'rgba(255, 215, 0, 0.15)',
  },
  tabText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#808080',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#FFD700',
  },
  contentSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#808080',
    marginBottom: 16,
  },
  courseCard: {
    marginBottom: 12,
    borderRadius: 16,
    overflow: 'hidden',
  },
  courseGradient: {
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  courseHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  categoryIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  courseInfo: {
    flex: 1,
  },
  courseTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  courseInstructor: {
    fontSize: 12,
    color: '#808080',
    marginTop: 2,
  },
  difficultyBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  courseDescription: {
    fontSize: 13,
    color: '#A0A0A0',
    marginBottom: 12,
    lineHeight: 18,
  },
  courseFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  courseStats: {
    flexDirection: 'row',
  },
  courseStat: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 12,
  },
  courseStatText: {
    fontSize: 12,
    color: '#808080',
    marginLeft: 4,
  },
  courseReward: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 215, 0, 0.15)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  rewardText: {
    fontSize: 12,
    color: '#FFD700',
    fontWeight: '600',
    marginLeft: 4,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingText: {
    fontSize: 12,
    color: '#FFD700',
    marginLeft: 6,
    fontWeight: '600',
  },
  gamesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  gameCard: {
    width: (width - 48) / 2,
    marginBottom: 12,
    borderRadius: 16,
    overflow: 'hidden',
  },
  gameGradient: {
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    minHeight: 180,
  },
  gameIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  gameName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 6,
  },
  gameDescription: {
    fontSize: 11,
    color: '#A0A0A0',
    marginBottom: 12,
    lineHeight: 16,
  },
  gameFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  gameDifficulty: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  gameDifficultyText: {
    fontSize: 9,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  gameReward: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  gameRewardText: {
    fontSize: 12,
    color: '#FFD700',
    fontWeight: '600',
    marginLeft: 4,
  },
  gameTime: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  gameTimeText: {
    fontSize: 10,
    color: '#808080',
    marginLeft: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    overflow: 'hidden',
  },
  modalGradient: {
    padding: 24,
    paddingTop: 48,
    minHeight: 400,
  },
  closeButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  modalHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  modalIcon: {
    width: 80,
    height: 80,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
  },
  modalInstructor: {
    fontSize: 14,
    color: '#808080',
    marginTop: 4,
  },
  modalDescription: {
    fontSize: 14,
    color: '#A0A0A0',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 24,
  },
  modalStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 24,
  },
  modalStat: {
    alignItems: 'center',
  },
  modalStatValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 8,
  },
  modalStatLabel: {
    fontSize: 12,
    color: '#808080',
    marginTop: 4,
  },
  rewardInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 215, 0, 0.1)',
    padding: 12,
    borderRadius: 12,
    marginBottom: 24,
  },
  rewardInfoText: {
    fontSize: 14,
    color: '#FFD700',
    marginLeft: 8,
  },
  enrollButton: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  enrollGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  enrollButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1A1A2E',
    marginLeft: 8,
  },
  gameModalHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  gameModalIcon: {
    width: 100,
    height: 100,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  gameInfo: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 32,
  },
  gameInfoItem: {
    alignItems: 'center',
  },
  gameInfoValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 8,
  },
  gameInfoLabel: {
    fontSize: 12,
    color: '#808080',
    marginTop: 4,
  },
  playButton: {
    borderRadius: 16,
    overflow: 'hidden',
  },
  playGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  playButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginLeft: 8,
  },
  resultContainer: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  resultIcon: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  resultTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  resultCoins: {
    fontSize: 18,
    color: '#FFD700',
    marginBottom: 24,
  },
  playAgainButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
  },
  playAgainText: {
    fontSize: 16,
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
