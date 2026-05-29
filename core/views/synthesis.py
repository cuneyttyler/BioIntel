from rest_framework.views import APIView
from rest_framework.response import Response
from core.services import askcos


class RetroSynthesisView(APIView):
    def post(self, request):
        smiles = request.data.get('smiles', '')
        if not smiles:
            return Response({'error': 'smiles required'}, status=400)
        return Response(askcos.single_step_retro(smiles))


class SynthesisTreeView(APIView):
    def post(self, request):
        smiles = request.data.get('smiles', '')
        if not smiles:
            return Response({'error': 'smiles required'}, status=400)
        return Response(askcos.multi_step_tree(smiles))


class ForwardPredictionView(APIView):
    def post(self, request):
        reactants = request.data.get('reactants', '')
        if not reactants:
            return Response({'error': 'reactants required'}, status=400)
        reagents = request.data.get('reagents', '')
        solvent = request.data.get('solvent', '')
        return Response(askcos.forward_predict(reactants, reagents, solvent))


class ConditionRecommendView(APIView):
    def post(self, request):
        reactants = request.data.get('reactants', '')
        products = request.data.get('products', '')
        reaction_type = request.data.get('reaction_type', '')
        if not reactants and not reaction_type:
            return Response({'error': 'reactants or reaction_type required'}, status=400)
        return Response(askcos.recommend_conditions(reactants, products, reaction_type))


class BuyableCheckView(APIView):
    def get(self, request):
        smiles = request.query_params.get('smiles', '')
        if not smiles:
            return Response({'error': 'smiles required'}, status=400)
        return Response(askcos.check_buyable(smiles))
