import torch


class LogReg(torch.nn.Module):

    # inits weights to random values
    # ties init and dc weights if specified
    def _setup_weights(self):
        
        # setup init
        if (self.tie_init):
            self.init_W = Parameter(torch.randn(1).expand(self.output_dim, 1))
        else:
            self.init_W = Parameter(torch.randn(self.output_dim, 1))
            
        # setup cooccur
        self.cooc_W = Parameter(torch.randn(self.output_dim, self.input_dim_non_dc - 1))
        
        self.W = torch.cat((self.init_W, self.cooc_W), 1)
        
        # setup dc
        if self.input_dim_dc > 0:
            if (self.tie_dc):
                self.dc_W = Parameter(torch.randn(self.input_dim_dc).expand(self.output_dim, self.input_dim_dc))
            else:
                self.dc_W = Parameter(torch.randn(self.output_dim, self.input_dim_dc))
            
            self.W = torch.cat((self.W, self.dc_W), 1)
    
    
    def __init__(self, input_dim_non_dc, input_dim_dc, output_dim, tie_init, tie_dc):
        super(LogReg, self).__init__()
        
        self.input_dim_non_dc = input_dim_non_dc
        self.input_dim_dc = input_dim_dc
        self.output_dim = output_dim
        
        self.tie_init = tie_init
        self.tie_dc = tie_dc

        self._setup_weights()
        
        
    def forward(self, X, index, mask):

        # reties the weights - need to do on every pass
        if self.input_dim_dc > 0:
            self.W = torch.cat((self.init_W.expand(self.output_dim, 1), self.cooc_W,
                               self.dc_W.expand(self.output_dim, self.input_dim_dc)), 1)
        else:
            self.W = torch.cat((self.init_W.expand(self.output_dim, 1), self.cooc_W), 1)
            
            
        # calculates n x l matrix output
        output = X.mul(self.W)
        output = output.sum(2)
        
        # changes values to extremely negative and specified indices
        if index is not None and mask is not None:
            output.index_add_(0, index, mask)
            
        return output
    
class SoftMax:

    def __init__(self, dataengine, dataset):
        self.dataengine = dataengine
        self.dataset = dataset
        dataframe_offset = self.dataengine.get_table_to_dataframe("Dimensions_clean", self.dataset)
        list = dataframe_offset.collect()
        dimension_dict = {}
        for dimension in list:
            dimension_dict[dimension['dimension']] = dimension['length']


        # X Tensor Dimensions (N * M * L)
        self.M = dimension_dict['M']
        self.N = dimension_dict['N']                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
        self.L = dimension_dict['L']

        # pytorch tensors
        self.X = None
        self._setupX()
        self.mask = None
        self._setupMask()
      #  self.W = None
      #  self._setupW()
        
        return

    # Will create the X-value tensor of size nxmxl
    def _setupX(self):
        coordinates = torch.LongTensor()
        values = torch.LongTensor([])
        feature_table = self.dataengine.get_table_to_dataframe("Feature_clean", self.dataset).collect()
        for factor in feature_table:
            coordinate = torch.LongTensor([[int(factor.vid) - 1], [int(factor.feature) - 1],
                                           [int(factor.assigned_val) - 1]])
            coordinates = torch.cat((coordinates, coordinate), 1)
            value = factor['count']
            values = torch.cat((values, torch.LongTensor([value])), 0)
        self.X = torch.sparse.LongTensor(coordinates, values, torch.Size([self.N, self.M, self.L]))
        print(self.X.to_dense())
        return

    def _setupMask(self, clean = 1):
        lookup = "Kij_lookup_clean" if clean else "Kij_lookup_clean"
        K_ij_lookup = self.dataengine.get_table_to_dataframe(
            lookup, self.dataset).select("vid", "k_ij").collect()
        self.mask = torch.zeros(self.N, self.L)
        for domain in K_ij_lookup:
            if domain.k_ij < self.L:
                self.mask[domain.vid, domain.k_ij:] = -10e6;
        print(self.mask)
        return

    # creates the W tensor of size m x l
    def _setupW(self):
        # Theo said all weights for one feature should start the same
        # Not tied for the init/cooccur but should still begin at same point
        
        # set up weight matrix for non DC cols. These weights are not tied
        non_DC_W = torch.randn(self.M - self.DC_count, self.L).type(torch.LongTensor)

        # set up weight matrix for DCs with weights tied along the row
        DC_col = torch.randn(self.DC_count).type(torch.LongTensor)
        DC_W = DC_col.repeat(self.L, 1).t()
        
        self.W = torch.cat((non_DC_W, DC_W), 0)

        return

    '''def train(model, loss, optimizer, x_val, y_val):
        x = Variable(x_val, requires_grad=False)
        y = Variable(y_val, requires_grad=False)

        # Reset gradient
        optimizer.zero_grad()

        fx = model.forward(x)
        output = loss.forward(fx, y)

        output.backward()

        optimizer.step()

        return output.data[0]

    def predict(model, x_val):
        x = Variable(x_val, requires_grad=False)
        output = model.forward(x)
        return output.data.numpy().argmax(axis=1)

    def main():

        clean_table = self.dataengine.get_table_to_dataframe("C_clean", self.dataset).collect()
        
        n_samples = self.N
        n_features = self.M
        n_classes = self.L
        
        model = CustomLogReg(n_samples, n_classes)
        loss = torch.nn.CrossEntropyLoss(size_average=True)
        optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)

        batch_size = 100

        for i in range(100):
            cost = 0.
            num_batches = n_samples // batch_size
            for k in range(num_batches):
                start, end = k * batch_size, (k + 1) * batch_size
                cost += train(model, loss, optimizer, X[start:end, :, :], 'I dont know what to put here')
'''
