import {
  QuestionMarkCircleIcon,
  MicrophoneIcon,
  CircleStackIcon,
} from '@heroicons/react/24/outline';

function HomePage() {
  return (
    <div
      className="flex flex-col items-center justify-center h-screen
     px-2"
    >
      <h1 className="text-4xl sm:text-5xl font-bold mb-8 sm:mb-16">
        SurveyGPT
      </h1>
      <div className="max-w-2xl space-y-3">
        <div className="infoCard">
          <QuestionMarkCircleIcon className="w-8 mr-3" />
          <p className="text-base sm:text-xl">
            Receive personalized survey questions
          </p>
        </div>
        <div className="infoCard">
          <MicrophoneIcon className="w-8 mr-3" />
          <p className="text-base sm:text-xl">
            Answer with audio or text inputs
          </p>
        </div>
        <div className="infoCard">
          <CircleStackIcon className="w-8 mr-3" />
          <p className="text-base sm:text-xl">
            Messages are stored in Firebase’s Firestore
          </p>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
